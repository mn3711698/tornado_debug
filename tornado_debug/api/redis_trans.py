# coding:utf8
import json
import types
import time

from .transaction import TransactionNode, Transaction


class RedisTransNode(TransactionNode):

    def __init__(self, name):
        self.command = {}
        return super(TransactionNode, self).__init__(name)

    def stop(self, *args, **kwargs):
        self.running = False
        time_use = time.time() - float(self.start_time)
        self.time += time_use
        self.is_start = False

    def record_command(self, time_use, *args, **kwargs):
        args_trans, kwargs_trans = self._trans_args(args, kwargs)
        key = self._get_args_str(args_trans, kwargs_trans)
        data = self.command.get(key, {'count': 0, 'time': 0})
        data['count'] += 1
        data['time'] += time_use
        self.command[key] = data

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


class RedisTransactionContext(object):

    def __init__(self, full_name, *args, **kwargs):
        self.full_name = full_name
        self.transaction = None
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        if Transaction.active:
            self.parent = Transaction.current
            self.transaction = self.parent.children.get(self.full_name, RedisTransNode(self.full_name))
            self.transaction.start()
            self.parent.children[self.full_name] = self.transaction
            Transaction.set_current(self.transaction)
            return self.transaction

    def __exit__(self, exc, value, tb):
        if Transaction.active:
            self.transaction.stop()
            Transaction.set_current(self.parent)
            self.transaction.record_command(*self.args, **self.kwargs)
