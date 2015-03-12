# coding: utf8
import functools
import time
import json
import logging

from tornado_debug.utils import resolve_path
from tornado_debug.import_hook import register_import_hook

logger = logging.getLogger(__name__)


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

    def __init__(self, name):
        DataCollecter.instances.append(self)
        # record function invoke count and time in all
        # eg: self.hooked_func = {"func_name": {'count':1, 'time': 200}, ...}
        self.hooked_func = {}
        self.name = name

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = self.hooked_func.get(full_name, None) or {'count': 0, "time": 0, "running": False, "start": 0}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            self.hooked_func[full_name] = data
            result = func(*args, **kwargs)
            data['time'] = round(data['time'] + (time.time() - data['start'])*1000, 2)
            data['running'] = False
            return result

        return wrapper

    def clear(self):
        self.time_use = 0
        for func_name, data in self.hooked_func.items():
            data['count'] = 0
            data['time'] = 0

    def render_data(self):
        return self.hooked_func

    @classmethod
    def render(cls):
        result = {}
        for collecter in cls.instances:
            result[collecter.name] = collecter.render_data()
        return json.dumps(result)
