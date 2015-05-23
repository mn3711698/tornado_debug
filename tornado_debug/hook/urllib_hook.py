# coding: utf8
import functools
import six

from . import DataCollecter, regist_wrap_module_func_hook, jinja_env
from tornado_debug.api.urllib_trans import UrllibTransContext, UrllibTransNode


class UrlLibDataCollecter(DataCollecter):

    def wrap_function(self, func):
        """
        only wrap urlopen
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            url = args[0]
            if not isinstance(url, six.string_types):
                url = url.get_full_url()
            with UrllibTransContext(url):
                return func(*args, **kwargs)

        return wrapper

    def render_data(self):
        func = UrllibTransNode.get_result()
        panel = {'urls': func}
        template = jinja_env.get_template('urllib.html')
        return template.render(panel=panel)


urllib23_data_collecter = UrlLibDataCollecter('UrlLib', 'urllib')


def regist_urllib_hook():
    regist_wrap_module_func_hook('urllib', 'urlopen', urllib23_data_collecter.wrap_function)
    regist_wrap_module_func_hook('urllib2', 'urlopen', urllib23_data_collecter.wrap_function)
