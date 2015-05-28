# coding:utf8
import functools

from . import DataCollecter, regist_wrap_module_func_hook
from tornado_debug.api.redis_trans import RedisTransactionContext, RedisTransNode


class RedisDataCollecter(DataCollecter):

    template = 'redis.html'

    def __init__(self, name, id):
        super(RedisDataCollecter, self).__init__(name, id)

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(instance, *args, **kwargs):
            with RedisTransactionContext(full_name, *args, **kwargs):
                return func(instance, *args, **kwargs)

        return wrapper

    def raw_data(self, request):
        func, commands = RedisTransNode.get_result(request)
        panel = {'func': func, 'commands': commands}
        return panel


redis_data_collecter = RedisDataCollecter("Redis", "Redis")


_redis_client_methods = ('bgrewriteaof', 'bgsave', 'client_kill',
    'client_list', 'client_getname', 'client_setname', 'config_get',
    'config_set', 'config_resetstat', 'config_rewrite', 'dbsize',
    'debug_object', 'echo', 'flushall', 'flushdb', 'info', 'lastsave',
    'object', 'ping', 'save', 'sentinel', 'sentinel_get_master_addr_by_name',
    'sentinel_master', 'sentinel_masters', 'sentinel_monitor',
    'sentinel_remove', 'sentinel_sentinels', 'sentinel_set',
    'sentinel_slaves', 'shutdown', 'slaveof', 'slowlog_get',
    'slowlog_reset', 'time', 'append', 'bitcount', 'bitop', 'bitpos',
    'decr', 'delete', 'dump', 'exists', 'expire', 'expireat', 'get',
    'getbit', 'getrange', 'getset', 'incr', 'incrby', 'incrbyfloat',
    'keys', 'mget', 'mset', 'msetnx', 'move', 'persist', 'pexpire',
    'pexpireat', 'psetex', 'pttl', 'randomkey', 'rename', 'renamenx',
    'restore', 'set', 'setbit', 'setex', 'setnx', 'setrange', 'strlen',
    'substr', 'ttl', 'type', 'watch', 'unwatch', 'blpop', 'brpop',
    'brpoplpush', 'lindex', 'linsert', 'llen', 'lpop', 'lpush',
    'lpushx', 'lrange', 'lrem', 'lset', 'ltrim', 'rpop', 'rpoplpush',
    'rpush', 'rpushx', 'sort', 'scan', 'scan_iter', 'sscan',
    'sscan_iter', 'hscan', 'hscan_inter', 'zscan', 'zscan_iter', 'sadd',
    'scard', 'sdiff', 'sdiffstore', 'sinter', 'sinterstore',
    'sismember', 'smembers', 'smove', 'spop', 'srandmember', 'srem',
    'sunion', 'sunionstore', 'zadd', 'zcard', 'zcount', 'zincrby',
    'zinterstore', 'zlexcount', 'zrange', 'zrangebylex',
    'zrangebyscore', 'zrank', 'zrem', 'zremrangebylex',
    'zremrangebyrank', 'zremrangebyscore', 'zrevrange',
    'zrevrangebyscore', 'zrevrank', 'zscore', 'zunionstore', 'pfadd',
    'pfcount', 'pfmerge', 'hdel', 'hexists', 'hget', 'hgetall',
    'hincrby', 'hincrbyfloat', 'hkeys', 'hlen', 'hset', 'hsetnx',
    'hmset', 'hmget', 'hvals', 'publish', 'eval', 'evalsha',
    'script_exists', 'script_flush', 'script_kill', 'script_load',
    'setex', 'lrem', 'zadd')

# redis.client.Redis的大多数命令都是通过基类StrictRedis实现的，除了下面的几个命令
# 所以这几个命令除了在StrictRedis上监控还要在Redis上监控，这样不论程序中使用StrictRedis
# 还是Redis, 都能监控到所有的命令
_compatibility_method_in_redis = ['setex', 'lrem', 'zadd']


def regist_redis_client_hook():
    for method in _redis_client_methods:
        # 构造独一无二的方法名
        full_name = "_tb_redis_%s" % method
        wrapper_factory = functools.partial(redis_data_collecter.wrap_function, full_name=full_name)
        regist_wrap_module_func_hook("redis.client", "StrictRedis.%s" % method, wrapper_factory)
        if method in _compatibility_method_in_redis:
            regist_wrap_module_func_hook("redis.client", "Redis.%s" % method, wrapper_factory)
