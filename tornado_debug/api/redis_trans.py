# coding:utf8
import json
import types
import time

from .transaction import TransactionNode, Transaction
from .utils import get_sorted_data


class RedisTransNode(TransactionNode):

    final_func_result = {}
    final_command_result = {}

    def __init__(self, name):
        self.command = {}
        return super(RedisTransNode, self).__init__(name)

    def stop(self, *args, **kwargs):
        self.running = False
        time_use = time.time() - float(self.start_time)
        self.time += time_use
        self.is_start = False
        self._record_command(time_use, *args, **kwargs)

    def _record_command(self, time_use, *args, **kwargs):
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

    def classify(self):
        cls = RedisTransNode
        node = self
        func_data = cls.final_func_result.get(node.name, {'count': 0, 'time': 0})
        func_data['count'] += node.count
        func_data['time'] += node.time
        cls.final_func_result[node.name] = func_data

        command_data = cls.final_command_result.get(node.name, {})
        cls.final_command_result[node.name] = command_data
        for args, data in node.command.items():
            args_data = command_data.get(args, {'count': 0, 'time': 0})
            command_data[args] = args_data
            args_data['count'] += data['count']
            args_data['time'] += data['time']

    @classmethod
    def get_result(cls):
        cls.final_func_result = get_sorted_data(cls.final_func_result)
        for func, data in cls.final_command_result.items():
            cls.final_command_result[func] = get_sorted_data(data)
        return cls.final_func_result, cls.final_command_result

    @staticmethod
    def clear():
        RedisTransNode.final_func_result = {}
        RedisTransNode.final_command_result = {}


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
            self.transaction.stop(*self.args, **self.kwargs)
            Transaction.set_current(self.parent)
