# coding:utf8
import functools

from . import DataCollecter, regist_wrap_module_func_hook
from tornado_debug.api.httpclient_trans import HttpClientTransNode, HttpClientTransContext


class TorndoHttpRequestCollecter(DataCollecter):

    template = 'http_client.html'

    def __init__(self, name, id):
        super(TorndoHttpRequestCollecter, self).__init__(name, id)

    def raw_data(self, request):
        panel = {'requests': HttpClientTransNode.get_result(request)}
        return panel


def HTTPConnection_run_callback_hook(func):
    """
    HTTPConnection._run_callback
    """
    @functools.wraps(func)
    def wrapper(self, response):
        request = response.request
        code = response.code
        request_time = response.request_time
        node = getattr(request, '_td_httpclient_node', None)
        if node:
            node.add_request(request.url, code, round(request_time*1000, 2))
        return func(self, response)
    return wrapper


def SimpleAsyncHTTPClient_fetch_hook(func):
    """
    fetch 之前在request上存储上下文节点
    """
    @functools.wraps(func)
    def wrapper(self, request, *args, **kwargs):
        with HttpClientTransContext('tornado.simple_httpclient.SimpleAsyncHTTPClient.fetch') as context:
            if context:
                from tornado.httpclient import HTTPRequest
                if not isinstance(request, HTTPRequest):
                    request = HTTPRequest(url=request, **kwargs)
                request._td_httpclient_node = context
            return func(self, request, *args, **kwargs)
    return wrapper


http_client_collector = TorndoHttpRequestCollecter("Tornado_SimpleHttpClient", "Tornado_SimpleHttpClient")


def regist_tornado_http_client_hook():
    regist_wrap_module_func_hook("tornado.simple_httpclient", "SimpleAsyncHTTPClient.fetch",
                                 SimpleAsyncHTTPClient_fetch_hook)
    regist_wrap_module_func_hook("tornado.simple_httpclient", "_HTTPConnection._run_callback",
                                 HTTPConnection_run_callback_hook)
