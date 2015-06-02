# coding:utf8
import tornado.ioloop
import tornado.web
import logging

from jinja2 import Environment, PackageLoader

from tornado_debug import config
from tornado_debug.hook import DataCollecter
from tornado_debug.hook.tornado_urls import urls as extra_urls
from tornado_debug.server.model import CollectedData

jinja_env = Environment(loader=PackageLoader('tornado_debug', 'templates'))
logger = logging.getLogger(__name__)


class StoreHandler(tornado.web.RequestHandler):
    def post(self):
        body = self.request.body
        CollectedData.save(body)
        return


class ListHandler(tornado.web.RequestHandler):
    def get(self):
        info_list = CollectedData.get_info_list()
        template = jinja_env.get_template("server/list.html")
        self.write(template.render(info_list=info_list))


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        template = jinja_env.get_template("server/index.html")
        self.write(template.render())


class DetailHandler(tornado.web.RequestHandler):
    def get(self, id):
        data = CollectedData.get_detail(id)
        if not data:
            raise tornado.web.HTTPError(404)
        self.write(DataCollecter.render_from_json(data))


# API HANDLERS
class ListApiHander(tornado.web.RequestHandler):
    def get(self):
        url = self.get_arguments('url')
        infos = CollectedData.get_info_list(url)
        self.write(infos)


def run():
    from tornado.options import parse_command_line
    parse_command_line()

    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/store", StoreHandler),
        (r"/list", ListHandler),
        (r"/detail/(\d+)", DetailHandler),
        (r"/api/list", ListApiHander),
    ] + extra_urls)
    application.listen(config.SERVER_PORT)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    run()
