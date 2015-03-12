# coding: utf8
import functools
import logging
import time
import json
import inspect
from collections import deque

from . import regist_wrap_module_func_hook

logger = logging.getLogger(__name__)


class TornadoDataCollecter(object):

    def __init__(self):
        self.time_use = None
        # record function invoke count and time in all
        # eg: self.hook_func = {"func_name": {'count':1, 'time': 200}, ...}
        self.hook_func = {}
        # record hooked class
        self.hooked_class = set()

    def hook_user_handler_func(self, handler_class):
        if handler_class in self.hooked_class:
            return
        handler_class_deq = deque()
        handler_class_deq.append(handler_class)
        while len(handler_class_deq):
            handler_class = handler_class_deq.popleft()
            if handler_class in self.hooked_class:
                continue
            for name in vars(handler_class):
                func = vars(handler_class)[name]
                if not callable(func):
                    continue
                if getattr(func, "_tm_is_async", False):
                    continue
                func_full_name = "%s.%s.%s" % (handler_class.__module__, handler_class.__name__, func.__name__)
                setattr(handler_class, name, self.wrap_function(func, func_full_name))
            for base_class in inspect.getmro(handler_class)[1:]:
                full_name = "%s.%s" % (base_class.__module__, base_class.__name__)
                if full_name not in ('__builtin__.object', 'tornado.web.RequestHandler'):
                    handler_class_deq.append(base_class)
            self.hooked_class.add(handler_class)

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = self.hook_func.get(full_name, None) or {'count': 0, "time": 0, "running": False, "start": 0}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            self.hook_func[full_name] = data
            result = func(*args, **kwargs)
            data['time'] = round(data['time'] + (time.time() - data['start'])*1000, 2)
            data['running'] = False
            return result

        return wrapper

    def clear(self):
        self.time_use = 0
        for func_name, data in self.hooked_class.items():
            data['count'] = 0
            data['time'] = 0

    def record_data(self):
        logger.info("time use: %s ms", self.time_use)
        for name, data in self.hook_func.items():
            if data['count']:
                logger.info("%s %s", name, json.dumps(data))


tornado_data_collecter = TornadoDataCollecter()


#def httpserver_httpconnection_finish_request(original):
#    @functools.wraps(original)
#    def wrapper(*args, **kwargs):
#        tornado_data_collecter.time_use = round(args[0]._request.request_time()*1000, 2)
#        original(*args, **kwargs)
#    return wrapper


def httpserver_httpconnection_on_headers(original):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        tornado_data_collecter.clear()
        original(*args, **kwargs)
    return wrapper


def web_request_handler_finish_hook(original):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        for name, data in tornado_data_collecter.hook_func.items():
            if data['running']:
                data['time'] = round(data['time'] + (time.time() - data['start'])*1000, 2)
        result = {'reqeust time': round(args[0].request.request_time()*1000, 2), 'func': tornado_data_collecter.hook_func}
        original(args[0], json.dumps(result))

    return wrapper

#def web_reqeust_handler_execute_hook(original):
#    """
#    bug: if _execute is not the last step of handler, the data collected is not completed
#    """
#    @functools.wraps(original)
#    def wrapper(*args, **kwargs):
#        original(*args, **kwargs)
#        tornado_data_collecter.record_data()

#    return wrapper


def web_application_init_hook(original):

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        handlers = []
        if len(args) > 1:
            handlers = args[1]
        elif kwargs:
            handlers = kwargs.get('handlers')
        for spec in handlers:
            assert isinstance(spec, tuple)
            assert len(spec) in (2, 3)
            handler_class = spec[1]
            tornado_data_collecter.hook_user_handler_func(handler_class)
        return original(*args, **kwargs)

    return wrapper


def web_asynchronous_hook(original):

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        args[0]._tm_is_async = True
        return original(*args, **kwargs)

    return wrapper


def gen_engine_hook(original):

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        args[0]._tm_is_async = True
        return original(*args, **kwargs)

    return wrapper


def register_tornaodo_hook():
    # regist_wrap_module_func_hook('tornado.httpserver', 'HTTPConnection._finish_request', httpserver_httpconnection_finish_request)
    # regist_wrap_module_func_hook('tornado.web', 'RequestHandler._execute', web_reqeust_handler_execute_hook)
    regist_wrap_module_func_hook('tornado.web', 'RequestHandler.finish', web_request_handler_finish_hook)
    regist_wrap_module_func_hook('tornado.web', 'Application.__init__', web_application_init_hook)
    regist_wrap_module_func_hook('tornado.web', 'asynchronous', web_asynchronous_hook)
    regist_wrap_module_func_hook('tornado.gen', 'engine', gen_engine_hook)
