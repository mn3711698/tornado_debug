# coding: utf8
import functools
import logging
import inspect
from collections import deque
import time
import re
import json

from . import regist_wrap_module_func_hook, DataCollecter, jinja_env
from .tornado_urls import urls

logger = logging.getLogger(__name__)

_HTML_TYPES = ('text/html', 'application/xhtml+xml')


def is_ajax_request(request):
    if 'X-Requested-With' in request.headers:
        return True
    return False


def is_html_response(response):
    content_type = response._headers.get('Content-Type', '').split(';')[0]
    if content_type not in _HTML_TYPES:
        return False
    return True


class TornadoDataCollecter(DataCollecter):

    def __init__(self, name, id):
        self.time_use = None
        # record hooked class
        self.hooked_class = set()
        super(TornadoDataCollecter, self).__init__(name, id)
        self.current_node = self.hooked_func

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
            parent_node = self.current_node
            data = parent_node.get(full_name, None) or {'count': 0, "time": 0, "running": False, "start": 0, 'children': {}}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            parent_node[full_name] = data
            try:
                self.current_node = data['children']
                result = func(*args, **kwargs)
            except Exception:
                raise
            finally:
                data['time'] = data['time'] + (time.time() - data['start'])
                data['running'] = False
                self.current_node = parent_node

            return result

        return wrapper

    def render_data(self):
        sorted_result = self._sort_result(self.hooked_func)
        panel = {'time_use': self.time_use, 'func': json.dumps(sorted_result)}
        template = jinja_env.get_template('tornado.html')
        return template.render(panel=panel)

    def _sort_result(self, funcs):
        funcs_list = []
        for name, data in funcs.items():
            if data['running']:
                data['time'] = data['time'] + (time.time() - data['start'])
            data['time'] = round(data['time']*1000, 2)
            funcs_list.append({'name': name, 'count': data['count'], 'time': data['time'], 'children': data['children']})
        funcs_list = sorted(funcs_list, key=lambda x: x['time'], reverse=True)

        for item in funcs_list:
            item['children'] = self._sort_result(item['children'])

        return funcs_list

    def clear(self):
        self.current_node = self.hooked_func = {}


tornado_data_collecter = TornadoDataCollecter("Tornado", "Tornado")


def httpserver_httpconnection_on_headers_hook(original):
    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        DataCollecter.clear_all()
        original(*args, **kwargs)
    return wrapper


def web_request_handler_finish_hook(original):
    @functools.wraps(original)
    def wrapper(self, chunk=None):
        if is_ajax_request(self.request) or not is_html_response(self) or getattr(self, 'is_tnDebug_inner', False):
            return original(self, chunk)
        else:
            tornado_data_collecter.time_use = round(self.request.request_time()*1000, 2)
            history_key = int(time.time())
            DataCollecter.set_history(history_key, DataCollecter.render())

            content_to_add = DataCollecter.get_content_to_add(history_key)
            insert_before_tag = r'</body>'
            pattern = re.escape(insert_before_tag)
            if chunk:
                bits = re.split(pattern, chunk, flags=re.IGNORECASE)
                if len(bits) > 1:
                    bits[-2] += content_to_add
                    chunk = insert_before_tag.join(bits)
                    if "Content-Length" in self._headers:
                        self.set_header("Content-Length", len(chunk))
            else:
                chunk = content_to_add
                if "Content-Length" in self._headers:
                    self.set_header("Content-Length", len(chunk))
            return original(self, chunk)
    return wrapper


def web_application_init_hook(original):

    @functools.wraps(original)
    def wrapper(self, handlers=None, *args,  **kwargs):
        #handlers = []
        #if len(args) > 1:
        #    handlers = args[1]
        #elif kwargs:
        #    handlers = kwargs.get('handlers')
        handlers.extend(urls)
        for spec in handlers:
            assert isinstance(spec, tuple)
            assert len(spec) in (2, 3)
            handler_class = spec[1]
            tornado_data_collecter.hook_user_handler_func(handler_class)
        return original(self, handlers, *args, **kwargs)

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
