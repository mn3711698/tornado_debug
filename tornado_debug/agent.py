# coding: utf8
import sys
import logging

from tornado_debug.import_hook import ImportHookFinder
from tornado_debug.hook.tornado_hook import register_tornaodo_hook
from tornado_debug.hook.redis_hook import regist_redis_client_hook
from tornado_debug.hook.urllib_hook import regist_urllib_hook

sys.meta_path.insert(0, ImportHookFinder())

logger = logging.getLogger(__name__)


def initialize():
    register_tornaodo_hook()
    regist_redis_client_hook()
    regist_urllib_hook()
