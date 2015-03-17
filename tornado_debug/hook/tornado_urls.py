# coding:utf8
import os

from tornado.web import StaticFileHandler

from tornado_debug import __file__ as root_directory

static_path = os.path.join(os.path.dirname(root_directory), 'static')

urls = [
    (r'/_tnDebug_/static/(.*)', StaticFileHandler, {"path": static_path}),
]
