# coding: utf8
import functools
import six
import time

from . import DataCollecter, regist_wrap_module_func_hook, jinja_env


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
            data = self.hooked_func.get(url, None) or {'count': 0, "time": 0, "running": False, "start": 0}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            self.hooked_func[url] = data
            result = func(*args, **kwargs)
            data['time'] = round(data['time'] + (time.time() - data['start'])*1000, 2)
            data['running'] = False
            return result

        return wrapper

    def render_data(self):
        func = super(UrlLibDataCollecter, self).render_data()
        panel = {'urls': func}
        template = jinja_env.get_template('urllib.html')
        return template.render(panel=panel)


urllib23_data_collecter = UrlLibDataCollecter('UrlLib', 'urllib')


def regist_urllib_hook():
    regist_wrap_module_func_hook('urllib', 'urlopen', urllib23_data_collecter.wrap_function)
    regist_wrap_module_func_hook('urllib2', 'urlopen', urllib23_data_collecter.wrap_function)
