# coding:utf8
import functools

from . import DataCollecter, regist_wrap_module_func_hook, jinja_env
from tornado_debug.api.httpclient_trans import HttpClientTransNode


class TorndoHttpRequestCollecter(DataCollecter):

    def __init__(self, name, id):
        super(TorndoHttpRequestCollecter, self).__init__(name, id)

    def wrap_function(self, func):
        @functools.wraps(func)
        def wrapper(instance, request, code, headers=None, buffer=None,
                    effective_url=None, error=None, request_time=None,
                    time_info=None):
            func(instance, request, code, headers, buffer, effective_url, error, request_time, time_info)
            HttpClientTransNode.add_request(request.url, code, round(request_time*1000, 2))
        return wrapper

    def raw_data(self):
        panel = {'requests': HttpClientTransNode.get_result()}
        return panel

    def render_data(self):
        panel = self.raw_data()
        template = jinja_env.get_template('http_client.html')
        return template.render(panel=panel)


http_client_collector = TorndoHttpRequestCollecter("Tornado_SimpleHttpClient", "Tornado_SimpleHttpClient")


def regist_tornado_http_request_hook():
    regist_wrap_module_func_hook("tornado.httpclient", "HTTPResponse.__init__",
                                 http_client_collector.wrap_function)
