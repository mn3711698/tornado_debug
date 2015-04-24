# coding: utf8
import functools
import time
import logging
from collections import deque

from jinja2 import Environment, PackageLoader

from tornado_debug.utils import resolve_path
from tornado_debug.import_hook import register_import_hook

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

    def clear(self):
        self.hooked_func = {}

    @classmethod
    def clear_all(cls):
        for instance in cls.instances:
            instance.clear()

    def raw_data(self):
        """
        统计的原始数据
        """
        func = []
        for name, data in self.hooked_func.items():
            if data['running']:
                data['time'] = data['time'] + (time.time() - data['start'])
            data['time'] = round(data['time']*1000, 2)
            func.append({'name': name, 'count': data['count'], 'time': data['time']})
        func = sorted(func, key=lambda x: x['time'], reverse=True)
        return func

    def render_data(self):
        """
        渲染统计的数据
        """
        return self.raw_data()

    def get_panel(self):
        return {'name': self.name, 'id': self.id, 'content': self.render_data()}

    @staticmethod
    def get_response_panel(response):
        """
        展示原始请求结果的pannel, 用于api的统计
        """
        template = jinja_env.get_template('response.html')
        content = template.render(response=response)
        return {'name': 'response', 'id': 'response', 'content': content}

    @classmethod
    def render(cls, response=None):
        """
        渲染页面
        """
        # result = {}
        # for collecter in cls.instances:
        #    result[collecter.name] = collecter.render_data()
        # return json.dumps(result)
        panels = [instance.get_panel() for instance in cls.instances]
        if response:
            panels.append(cls.get_response_panel(response))
        template = jinja_env.get_template('index.html')
        return template.render(panels=panels)

    def get_json_panel(self):
        return {'name': self.name, 'content': self.raw_data()}

    @classmethod
    def json(cls):
        result = {}
        for instance in cls.instances:
            panel = instance.get_json_panel()
            result[panel['name']] = panel['content']
        return result

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
