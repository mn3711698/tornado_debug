# coding: utf8
import functools
import json
import time
import logging
from collections import deque

from jinja2 import Environment, PackageLoader

from tornado_debug.utils import resolve_path
from tornado_debug.import_hook import register_import_hook
from tornado_debug.api.transaction import (
    TransactionNode, NodeClasses, Transaction
)

logger = logging.getLogger(__name__)

jinja_env = Environment(loader=PackageLoader('tornado_debug', 'templates'))


def wrap_module_func(module, attribute, wrapper_factory):
    try:
        (parent, attribute, original) = resolve_path(module, attribute)
    except AttributeError:
        logger.warning("Attribute error : %s  %s", module, attribute)
        return
    wrapper = wrapper_factory(original)
    setattr(parent, attribute, wrapper)


def regist_wrap_module_func_hook(module_str, attribute, wrapper_factory):
    register_import_hook(module_str, functools.partial(wrap_module_func, attribute=attribute, wrapper_factory=wrapper_factory))


class DataCollecter(object):

    instances = []
    history = deque()
    max_history = 5
    running = False

    template = ""  # 模版名称

    def __init__(self, name, id):
        DataCollecter.instances.append(self)
        # record function invoke count and time in all
        # eg: self.hooked_func = {"func_name": {'count':1, 'time': 200, chilidren:{}}, ...}
        self.hooked_func = {}
        self.name = name
        self.id = id

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = self.hooked_func.get(full_name, None) or {'count': 0, "time": 0, "running": False, "start": 0}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            self.hooked_func[full_name] = data
            result = func(*args, **kwargs)
            data['time'] = data['time'] + (time.time() - data['start'])
            data['running'] = False
            return result

        return wrapper

    @classmethod
    def clear_all(cls, request):
        for node_cls in NodeClasses:
            node_cls.clear(request)
        # 先清理node, 再stop Transaction, 因为node依赖request和transaction的对应关系
        Transaction.stop(request)

    def raw_data(self, request):
        """
        统计的原始数据
        """
        pass

    def render_data(self, raw_data):
        """
        渲染统计的数据
        """
        template = jinja_env.get_template(self.template)
        return template.render(panel=raw_data)

    def get_panel(self, request):
        raw_data = self.raw_data(request)
        return {'name': self.name, 'id': self.id, 'content': self.render_data(raw_data)}

    @staticmethod
    def get_response_raw_data(handler, response):
        """
        展示原始请求结果的pannel, 用于api的统计
        """
        url = handler.request.uri
        method = handler.request.method
        code = handler._status_code
        time_use = round(handler.request.request_time()*1000, 2)
        panel = {'url': url, 'method': method, 'code': code,
                 'time_use': time_use, 'response': response,
                 'start_time': handler.request._start_time}
        return panel

    @staticmethod
    def get_response_panel(raw_data):
        template = jinja_env.get_template('response.html')
        content = template.render(panel=raw_data)
        return {'name': 'response', 'id': 'response', 'content': content}

    @classmethod
    def render(cls, handler, response=""):
        """
        渲染页面
        """
        request = handler.request
        if not Transaction.get_root(request):
            return ""
        TransactionNode.trim_data(request)
        panels = [instance.get_panel(request) for instance in cls.instances]

        response_raw_data = cls.get_response_raw_data(handler, response)
        panels.append(cls.get_response_panel(response_raw_data))

        template = jinja_env.get_template('index.html')
        return template.render(panels=panels)

    def get_json_panel(self, request):
        return {'name': self.name, 'id': self.id, 'content': self.raw_data(request)}

    @classmethod
    def json(cls, handler, response=""):
        request = handler.request
        if not Transaction.get_root(request):
            return ""
        TransactionNode.trim_data(request)

        result = {}
        for instance in cls.instances:
            panel = instance.get_json_panel(handler.request)
            result[panel['id']] = panel

        response_panel_raw = cls.get_response_raw_data(handler, response)
        response_panel_json = {'name': 'response', 'id': 'response', 'content': response_panel_raw}
        result['response'] = response_panel_json
        return json.dumps(result)

    @classmethod
    def get_history(cls, key):
        for k, v in cls.history:
            if key == k:
                return v
        return ""

    @classmethod
    def set_history(cls, key, content):
        if len(cls.history) >= cls.max_history:
            cls.history.popleft()
        cls.history.append((key, content))

    @classmethod
    def get_content_to_add(cls, history_key):
        template = jinja_env.get_template("handle.html")
        return template.render(history_key=history_key)
