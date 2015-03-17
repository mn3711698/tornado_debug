# coding:utf8
import os

from tornado.web import StaticFileHandler, RequestHandler

from tornado_debug import __file__ as root_directory
from . import DataCollecter

static_path = os.path.join(os.path.dirname(root_directory), 'static')


class IndexHandler(RequestHandler):
    def get(self, key):
        key = int(key)
        content = DataCollecter.get_history(key)
        self.write(content)


class InnerStaticFileHandler(StaticFileHandler):
    pass


IndexHandler.is_tnDebug_inner = True
InnerStaticFileHandler.is_tnDebug_inner = True

urls = [
    (r'/_tnDebug_/static/(.*)', InnerStaticFileHandler, {"path": static_path}),
    (r'/_tnDebug_/(\d+)/', IndexHandler),
]
