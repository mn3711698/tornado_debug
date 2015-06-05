# coding: utf8
import os
import ConfigParser
import json


# server config
REDIS_HOST = '10.13.81.183'
REDIS_PORT = '6379'
SERVER_PORT = 8888
URL_PREFIX = ["/", "/n/", "/p/", "/ic/index", "/cl/", "/cr/", "/c/", "/api/", "/f/"]
RECORDE_INTERVAL_SECONDS = 60

# agent config
SERVER_MODE = os.environ.get('TOR_DEBUG_SERVER_MODE') == '1'
SERVER_DOMAIN = ''
FORBIDDEN_METHODS = ['POST']
ABNORMAL_REQUEST_TIME = 1000


def _prepare():
    config_path = os.path.join(os.path.expanduser('~'),  '.tornado_debug.conf')
    if os.path.exists(config_path):
        config = ConfigParser.RawConfigParser()
        config.read(config_path)
        global_settings = globals()
        for name, value in config.items('TORNADO_DEBUG'):
            name = name.upper()
            if name in global_settings:
                if name in ('SERVER_PORT', 'RECORDE_INTERVAL_SECONDS', 'ABNORMAL_REQUEST_TIME'):
                    value = int(value)
                if name in ('URL_PREFIX', 'FORBIDDEN_METHODS'):
                    value = json.loads(value)
                global_settings[name] = value

    global URL_PREFIX
    if '/' not in URL_PREFIX:
        URL_PREFIX.append('/')
    URL_PREFIX = sorted(URL_PREFIX, key=lambda x: len(x), reverse=True)

_prepare()

# agent settings
if not SERVER_DOMAIN:
    SERVER_DOMAIN = '127.0.0.1:%s' % SERVER_PORT
STORAGE_URL = "http://%s/store" % SERVER_DOMAIN
