# coding:utf8
import functools
import time
import json
import types

from . import DataCollecter, regist_wrap_module_func_hook, jinja_env


class RedisDataCollecter(DataCollecter):

    def __init__(self, name, id):
        super(RedisDataCollecter, self).__init__(name, id)
        self.commands = {}

    def wrap_function(self, func, full_name):
        @functools.wraps(func)
        def wrapper(instance, *args, **kwargs):
            data = self.hooked_func.get(full_name, None) or {'count': 0, "time": 0, "running": False, "start": 0}
            data['count'] += 1
            data['running'] = True
            data['start'] = time.time()
            self.hooked_func[full_name] = data

            command = self.commands.get(full_name, {})
            args_trans, kwargs_trans = self._trans_args(args, kwargs)
            key = self._get_args_str(args_trans, kwargs_trans)
            detail = command.get(key, {'count': 0, "time": 0})
            detail['count'] += 1
            command[key] = detail
            self.commands[full_name] = command

            result = func(instance, *args_trans, **kwargs_trans)

            end_time = time.time()
            data['time'] = data['time'] + (end_time - data['start'])
            data['running'] = False
            detail['time'] += (end_time - data['start'])
            return result

        return wrapper

    def raw_data(self):
        func = super(RedisDataCollecter, self).raw_data()
        commands = self._format_commands_result()
        panel = {'func': func, 'commands': commands}
        return panel

    def render_data(self):
        panel = self.raw_data()
        template = jinja_env.get_template('redis.html')
        return template.render(panel=panel)

    def _format_commands_result(self):
        result = {}
        for command, detail in self.commands.items():
            detail_list = [{'args': args, 'count': data['count'], 'time': round(data['time']*1000, 2)} for args, data in detail.items()]
            detail_list = sorted(detail_list, key=lambda x: x['time'], reverse=True)
            result[command] = detail_list

        return result

    def _trans_args(self, args, kwargs):
        # TODO: 此处期待有更好的解决方法
        args_trans = [self._iter_to_common_list(arg) for arg in args]
        kwargs_trans = {}
        for k, v in kwargs.items():
            kwargs_trans[k] = self._iter_to_common_list(v)
        return args_trans, kwargs_trans

    def _get_args_str(self, args, kwargs):
        # TODO: 此处期待有更好的解决方法
        return json.dumps({'args': args, 'kwargs': kwargs})

    def _iter_to_common_list(self, arg):
        if isinstance(arg, types.GeneratorType):
            return [n for n in arg]
        else:
            return arg

    def clear(self):
        super(RedisDataCollecter, self).clear()
        self.commands = {}


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
        wrapper_factory = functools.partial(redis_data_collecter.wrap_function, full_name=method)
        regist_wrap_module_func_hook("redis.client", "StrictRedis.%s" % method, wrapper_factory)
        if method in _compatibility_method_in_redis:
            regist_wrap_module_func_hook("redis.client", "Redis.%s" % method, wrapper_factory)
