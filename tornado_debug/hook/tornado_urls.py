# coding:utf8
import os

from tornado.web import StaticFileHandler, RequestHandler

from tornado_debug import __file__ as root_directory
from . import DataCollecter, jinja_env

static_path = os.path.join(os.path.dirname(root_directory), 'static')


class IndexHandler(RequestHandler):
    def get(self, key):
        key = int(key)
        content = DataCollecter.get_history(key)
        self.write(content)


class InnerStaticFileHandler(StaticFileHandler):
    pass


class FileListHandler(RequestHandler):
    def get(self):
        files = os.listdir('/Users/lianbo/tmpt')
        template = jinja_env.get_template('file_list.html')
        self.write(template.render(files=files))


IndexHandler.is_tnDebug_inner = True
InnerStaticFileHandler.is_tnDebug_inner = True
FileListHandler.is_tnDebug_inner = True

urls = [
    (r'/_tnDebug_/static/(.*)', InnerStaticFileHandler, {"path": static_path}),
    (r'/_tnDebug_/file/(.*)', InnerStaticFileHandler, {"path": "/Users/lianbo/tmpt"}),
    (r'/_tnDebug_/files/', FileListHandler),
    (r'/_tnDebug_/(\d+)/', IndexHandler),
]
