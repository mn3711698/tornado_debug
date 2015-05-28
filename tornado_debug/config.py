# coding: utf8
import os

SERVER_MODE = os.environ.get('TOR_DEBUG_SERVER_MODE') == '1'
STORAGE_URL = "http://127.0.0.1:8888/store"
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'

URL_PREFIX = ["/", "/n/", "/p/", "/ic/index", "/cl/", "/cr/", "/c/", "/api/", "/f/"]


def _prepare():
    global URL_PREFIX
    if '/' not in URL_PREFIX:
        URL_PREFIX.push('/')
    URL_PREFIX = sorted(URL_PREFIX, key=lambda x: len(x), reverse=True)


_prepare()
