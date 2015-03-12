# coding: utf8
import functools
import logging
import time
import inspect
from collections import deque

from . import regist_wrap_module_func_hook, DataCollecter

logger = logging.getLogger(__name__)


class TornadoDataCollecter(DataCollecter):

    def __init__(self, name):
        self.time_use = None
        # record hooked class
        self.hooked_class = set()
        super(TornadoDataCollecter, self).__init__(name)

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

    def render_data(self):
        for name, data in tornado_data_collecter.hooked_func.items():
            if data['running']:
                data['time'] = round(data['time'] + (time.time() - data['start'])*1000, 2)
        result = {'reqeust time': self.time_use, 'func': self.hooked_func}
        return result


tornado_data_collecter = TornadoDataCollecter("Tornado")


def httpserver_httpconnection_on_headers_hook(original):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        tornado_data_collecter.clear()
        original(*args, **kwargs)
    return wrapper


def web_request_handler_finish_hook(original):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        tornado_data_collecter.time_use = round(args[0].request.request_time()*1000, 2)
        original(args[0], DataCollecter.render())

    return wrapper


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
    regist_wrap_module_func_hook('tornado.httpserver', 'HTTPConnection._on_headers', httpserver_httpconnection_on_headers_hook)
    regist_wrap_module_func_hook('tornado.web', 'RequestHandler.finish', web_request_handler_finish_hook)
    regist_wrap_module_func_hook('tornado.web', 'Application.__init__', web_application_init_hook)
    regist_wrap_module_func_hook('tornado.web', 'asynchronous', web_asynchronous_hook)
    regist_wrap_module_func_hook('tornado.gen', 'engine', gen_engine_hook)
