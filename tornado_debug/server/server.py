# coding:utf8
import tornado.ioloop
import tornado.web
import logging
from datetime import datetime, timedelta
import time

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
        max_time = time.time()
        min_time = max_time - 24*3600
        info_list = CollectedData.get_info_list(max_time, min_time)
        template = jinja_env.get_template("server/list.html")
        self.write(template.render(info_list=info_list))


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        template = jinja_env.get_template("server/index.html")
        self.write(template.render(urls=config.URL_PREFIX))


class DetailHandler(tornado.web.RequestHandler):
    def get(self, id):
        data = CollectedData.get_detail(id)
        if not data:
            raise tornado.web.HTTPError(404)
        self.write(DataCollecter.render_from_json(data))


# API HANDLERS
class ListApiHander(tornado.web.RequestHandler):
    def get_data_of_the_day(self, now, urls):
        max_time = time.mktime(now.timetuple())
        min_time = time.mktime(datetime(now.year, now.month, now.day).timetuple())
        infos = CollectedData.get_info_list(max_time, min_time, urls)
        return infos

    def get(self):
        urls = self.get_arguments('urls')
        now = datetime.now()
        infos = self.get_data_of_the_day(now, urls)
        self.write(infos)


class CompareListApiHander(ListApiHander):
    def get(self):
        url = self.get_argument('url')
        if not url:
            raise tornado.web.HTTPError(404)

        result = {}
        now = datetime.now()
        infos = self.get_data_of_the_day(now, [url])
        result[now.strftime("%Y-%m-%d")] = infos[url]

        yesterday = now - timedelta(days=1)
        infos = self.get_data_of_the_day(yesterday, [url])
        result[yesterday.strftime("%Y-%m-%d")] = infos[url]

        last_week = now - timedelta(days=7)
        infos = self.get_data_of_the_day(last_week, [url])
        result[last_week.strftime("%Y-%m-%d")] = infos[url]

        self.write(result)


def run():
    from tornado.options import parse_command_line
    parse_command_line()

    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/store", StoreHandler),
        (r"/list", ListHandler),
        (r"/detail/(\d+)", DetailHandler),
        (r"/api/list", ListApiHander),
        (r"/api/list/compare", CompareListApiHander),
    ] + extra_urls)
    application.listen(config.SERVER_PORT)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    run()
