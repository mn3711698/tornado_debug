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
from tornado_debug import config
from tornado_debug.api.transaction import (
    Transaction, AsyncTransactionContext,
    SyncTransactionContext, AsyncCallbackContext,
    TransactionNode
)

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


def is_json_response(response):
    content_type = response._headers.get('Content-Type', '').split(';')[0]
    return content_type == 'text/json'


# copy from tornado/escape.py:157
_UTF8_TYPES = (bytes, type(None))


def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    assert isinstance(value, unicode)
    return value.encode("utf-8")


class TornadoDataCollecter(DataCollecter):

    def __init__(self, name, id):
        self.time_use = None
        # record hooked class
        self.hooked_class = set()
        super(TornadoDataCollecter, self).__init__(name, id)

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
                func = getattr(handler_class, name)
                raw_func = vars(handler_class)[name]
                if not callable(func):
                    continue
                func_full_name = "%s.%s.%s" % (handler_class.__module__, handler_class.__name__, func.__name__)
                if isinstance(raw_func, staticmethod):
                    wrapped_func = self.wrap_static_method(func, func_full_name)
                elif isinstance(raw_func, classmethod):
                    wrapped_func = self.wrap_class_method(func, func_full_name)
                else:
                    wrapped_func = self.wrap_function(func, func_full_name)
                setattr(handler_class, name, wrapped_func)
            for base_class in inspect.getmro(handler_class)[1:]:
                full_name = "%s.%s" % (base_class.__module__, base_class.__name__)
                if full_name not in ('__builtin__.object', 'tornado.web.RequestHandler'):
                    handler_class_deq.append(base_class)
            self.hooked_class.add(handler_class)

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with SyncTransactionContext(full_name):
                return func(*args, **kwargs)
        return wrapper

    def wrap_static_method(self, func, full_name):
        def wrapper(*args, **kwargs):
            with SyncTransactionContext(full_name):
                return func(*args, **kwargs)
        return staticmethod(wrapper)

    def wrap_class_method(self, func, full_name):
        def wrapper(cls, *args, **kwargs):
            with SyncTransactionContext(full_name):
                return func(*args, **kwargs)
        return classmethod(wrapper)

    def raw_data(self, request):
        func_result, flat_result = TransactionNode.get_result(request)
        return {'time_use': 0, 'func': func_result, 'flat': flat_result}

    def render_data(self, request):
        raw_data = self.raw_data(request)
        raw_data['func'] = json.dumps(raw_data['func'])
        template = jinja_env.get_template('tornado.html')
        return template.render(panel=raw_data)


tornado_data_collecter = TornadoDataCollecter("Tornado", "Tornado")


def web_application_call_hook(original):
    """
    application.__call__是开启监控的地方
    """
    @functools.wraps(original)
    def wrapper(self, request):
        Transaction.start(request)
        return original(self, request)
    return wrapper


def web_request_handler_finish_hook(original):
    @functools.wraps(original)
    def wrapper(self, chunk=None):
        try:
            if getattr(self, 'is_tnDebug_inner', False):
                return original(self, chunk)

            # server mode only response the debug data
            if config.SERVER_MODE:
                # self._write_buffer = []
                # self.write(DataCollecter.json())
                tornado_data_collecter.time_use = round(self.request.request_time()*1000, 2)
                result = utf8(DataCollecter.render(self.request))
                if result:
                    open('td_result/%s-[%s]' % (self.request.uri.replace('/', '#'), self.request._start_time), 'a').write(result)
                return original(self, chunk)

            if is_ajax_request(self.request) or not (is_html_response(self) or is_json_response(self)):
                # ajax请求、html和json其他格式的请求、tornado_debug内部请求不做特殊渲染
                return original(self, chunk)
            else:
                tornado_data_collecter.time_use = round(self.request.request_time()*1000, 2)

                if chunk:
                    self.write(chunk)
                origin_response = chunk = ("").join(self._write_buffer)

                insert_before_tag = r'</body>'
                pattern = re.escape(insert_before_tag)
                if chunk:
                    bits = re.split(pattern, chunk, flags=re.IGNORECASE)
                    if len(bits) > 1:
                        history_key = int(time.time())
                        history_val = utf8(DataCollecter.render(self.request))
                        DataCollecter.set_history(history_key, history_val)
                        # 因为可能先write, 再finish. 为了插入结果， 只能手动修改_write_buffer
                        # 放入_write_buffer的必须时utf8编码过的
                        content_to_add = utf8(DataCollecter.get_content_to_add(history_key))

                        bits[-2] += content_to_add
                        chunk = insert_before_tag.join(bits)
                    else:
                        # TODO: 对于非html的body，将统计结果和response一起渲染，期望有更好的解决方案
                        chunk = utf8(DataCollecter.render(self.request, origin_response))
                else:
                    chunk = utf8(DataCollecter.render(self.request, origin_response))
                if not is_html_response(self):
                    self.set_header('Content-Type', 'text/html')
                self._write_buffer = [chunk]
                return original(self, None)
        finally:
            Transaction.stop(self.request)  # 监控结束
            DataCollecter.clear_all(self.request)
    return wrapper


def web_application_init_hook(original):

    @functools.wraps(original)
    def wrapper(self, handlers=None, *args,  **kwargs):
        handlers.extend(urls)
        for spec in handlers:
            assert isinstance(spec, tuple)
            assert len(spec) in (2, 3)
            handler_class = spec[1]
            tornado_data_collecter.hook_user_handler_func(handler_class)
        return original(self, handlers, *args, **kwargs)

    return wrapper


def gen_runner_init_hook(original):
    @functools.wraps(original)
    def wrapper(self, *args,  **kwargs):
        self._tb_transaction = Transaction.get_current()
        return original(self, *args, **kwargs)
    return wrapper


def gen_runner_run_hook(original):
    @functools.wraps(original)
    def wrapper(self):
        transaction = getattr(self, '_tb_transaction', None)
        if transaction:
            with AsyncTransactionContext(transaction):
                return original(self)
        else:
            return original(self)
    return wrapper


def gen_runner_set_result_hook(original):
    @functools.wraps(original)
    def wrapper(self, key, result):
        with AsyncCallbackContext():
            return original(self, key, result)
    return wrapper


def simple_httpclient_SimpleAsyncHTTPClient_fetch(original):
    @functools.wraps(original)
    def wrapper(self, *args, **kwargs):
        with SyncTransactionContext("tornado.simple_httpclient.SimpleAsyncHTTPClient.fetch"):
            return original(self, *args, **kwargs)
    return wrapper


def register_tornaodo_hook():
    regist_wrap_module_func_hook('tornado.web', 'RequestHandler.finish', web_request_handler_finish_hook)
    regist_wrap_module_func_hook('tornado.web', 'Application.__init__', web_application_init_hook)
    regist_wrap_module_func_hook('tornado.web', 'Application.__call__', web_application_call_hook)
    regist_wrap_module_func_hook('tornado.gen', 'Runner.__init__', gen_runner_init_hook)
    regist_wrap_module_func_hook('tornado.gen', 'Runner.run', gen_runner_run_hook)
    regist_wrap_module_func_hook('tornado.gen', 'Runner.set_result', gen_runner_set_result_hook)
    #regist_wrap_module_func_hook('tornado.simple_httpclient', 'SimpleAsyncHTTPClient.fetch',
    #                             simple_httpclient_SimpleAsyncHTTPClient_fetch)
