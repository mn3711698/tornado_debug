# coding: utf8
import functools
import six

from . import DataCollecter, regist_wrap_module_func_hook, jinja_env
from tornado_debug.api.urllib_trans import UrllibTransContext, UrllibTransNode


class UrlLibDataCollecter(DataCollecter):

    def raw_data(self, request):
        func = UrllibTransNode.get_result(request)
        return {'urls': func}

    def render_data(self, request):
        panel = self.raw_data(request)
        template = jinja_env.get_template('urllib.html')
        return template.render(panel=panel)


urllib23_data_collecter = UrlLibDataCollecter('UrlLib', 'urllib')


def urlopen_hook(func):
    """
    only wrap urlopen
    """
    @functools.wraps(func)
    def wrapper(url, *args, **kwargs):
        if not isinstance(url, six.string_types):
            url = url.get_full_url()
        with UrllibTransContext(url):
            return func(url, *args, **kwargs)

    return wrapper


def regist_urllib_hook():
    regist_wrap_module_func_hook('urllib', 'urlopen', urlopen_hook)
    regist_wrap_module_func_hook('urllib2', 'urlopen', urlopen_hook)
