# coding: utf8
import sys
import logging

from tornado_debug.import_hook import ImportHookFinder
from tornado_debug.hook.tornado_hook import register_tornaodo_hook
from tornado_debug.hook.redis_hook import regist_redis_client_hook
#from tornado_debug.hook.urllib_hook import regist_urllib_hook
#from tornado_debug.hook.tornado_http_request import regist_tornado_http_request_hook

sys.meta_path.insert(0, ImportHookFinder())

logger = logging.getLogger(__name__)


def initialize():
    try:
        register_tornaodo_hook()
        logger.info("tornado init ok")
        regist_redis_client_hook()
        logger.info("redis init ok")
        #regist_urllib_hook()
        #logger.info("urllib init ok")
        #regist_tornado_http_request_hook()
        #logger.info("tornado http request inti ok")
    except Exception as e:
        logger.exception("%s", e)


if __name__ == "__main__":
    initialize()
