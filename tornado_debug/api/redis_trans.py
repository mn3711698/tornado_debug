# coding:utf8
import json
import types
import time

from .transaction import TransactionNode, Transaction
from .utils import get_sorted_data


class RedisTransNode(TransactionNode):

    requests_m_result = {}
    # request: {
    # final_func_result : {}
    # final_command_result : {}
    # }

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

    def classify(self, request):
        cls = RedisTransNode
        node = self

        if request not in cls.requests_m_result:
            cls.requests_m_result[request] = {'final_func_result': {}, 'final_command_result': {}}

        final_func_result = cls.requests_m_result[request]['final_func_result']
        final_command_result = cls.requests_m_result[request]['final_command_result']

        func_data = final_func_result.get(node.name, {'count': 0, 'time': 0})
        func_data['count'] += node.count
        func_data['time'] += node.time
        final_func_result[node.name] = func_data

        command_data = final_command_result.get(node.name, {})
        final_command_result[node.name] = command_data
        for args, data in node.command.items():
            args_data = command_data.get(args, {'count': 0, 'time': 0})
            command_data[args] = args_data
            args_data['count'] += data['count']
            args_data['time'] += data['time']

    @classmethod
    def get_result(cls, request):
        if request not in cls.requests_m_result:
            return [], []
        result = cls.requests_m_result[request]

        final_func_result = result['final_func_result']
        final_command_result = result['final_command_result']

        final_func_result = get_sorted_data(final_func_result)

        for func, data in final_command_result.items():
            final_command_result[func] = get_sorted_data(data)
        return final_func_result, final_command_result


class RedisTransactionContext(object):

    def __init__(self, full_name, *args, **kwargs):
        self.full_name = full_name
        self.transaction = None
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        if Transaction.is_active():
            self.parent = Transaction.current
            self.transaction = self.parent.children.get(self.full_name, RedisTransNode(self.full_name))
            self.transaction.start()
            self.parent.children[self.full_name] = self.transaction
            Transaction.set_current(self.transaction)
            return self.transaction

    def __exit__(self, exc, value, tb):
        if Transaction.is_active():
            self.transaction.stop(*self.args, **self.kwargs)
            Transaction.restore(self.parent)
