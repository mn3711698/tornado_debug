# coding: utf8
import time

from .utils import get_sorted_data


"""
Node 负责存储 ；Transation 负责调用Node
"""

NodeClasses = []


class NodeMeta(type):
    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        NodeClasses.append(cls)


class TransactionNode(object):
    """
    一次函数调用只使用一次start , stop
    对于异步函数，start , stop 之间有多次resume, 和 hangup
    """
    __metaclass__ = NodeMeta

    requests_m_result = {}
    # request: {
    # result : {}
    # flat_result : {}
    # url : ""
    # method : ""
    # code : 200
    # time : 0
    # }

    def __init__(self, name):
        self.count = 0
        self.running = False
        self.time = 0
        self.name = name
        self.children = {}
        self.start_time = 0
        # is_start 用于标记上是否已经调用了start
        self.is_start = False

    def start(self):
        """
        函数首次启动
        """
        self.running = True
        self.count += 1
        self.start_time = time.time()
        self.is_start = True

    def restart(self):
        """
        重启， 重置启动时间, 用于Task的callback
        """
        self.running = True
        self.start_time = time.time()
        self.is_start = True

    def stop(self):
        """
        关闭
        """
        self.running = False
        self.time += (time.time() - float(self.start_time))
        self.is_start = False

    def resume(self):
        """
        用于Runner.run, 统计异步执行
        """
        if self.is_start:
            return
        self.running = True
        self.start_time = time.time()

    def hang_up(self):
        """
        用于Runner.run, 统计异步执行
        """
        if self.is_start:
            return
        self.running = False
        self.time += (time.time() - float(self.start_time))

    def is_running(self):
        return self.running

    def classify(self, request):
        """
        子类进行特殊话处理
        """
        pass

    @classmethod
    def get_result(cls, request):
        result = cls.requests_m_result[request]
        return result['result'], result['flat_result']

    @classmethod
    def trim_data(cls, request):
        """
        渲染或者存储之前整理数据
        """
        root = Transaction.get_root(request)
        flat_result = {}
        result = cls._sort_result(root.children, flat_result, request)
        flat_result = get_sorted_data(flat_result)
        cls.requests_m_result[request] = {'result': result, 'flat_result': flat_result}

    @classmethod
    def _sort_result(cls, children_nodes, flat_result, request):
        funcs_list = []
        for name, node in children_nodes.items():
            if node.is_running():
                node.stop()
            node.classify(request) # node 分类处理
            # construtct flat result
            flat = flat_result.get(name, {"count": 0, 'time': 0})
            flat['count'] += node.count
            flat['time'] += node.time
            flat_result[name] = flat

            node.time = round(node.time*1000, 2)

            funcs_list.append({'name': name, 'count': node.count, 'time': node.time, 'children': node.children})
        funcs_list = sorted(funcs_list, key=lambda x: x['time'], reverse=True)

        for item in funcs_list:
            item['children'] = cls._sort_result(item['children'], flat_result, request)

        return funcs_list

    @classmethod
    def clear(cls, request):
        if request in cls.requests_m_result:
            del cls.requests_m_result[request]


class Transaction(object):
    requests_map_trans = {}  # {request: Transaction}
    current = None

    @classmethod
    def start(cls, request):
        assert request not in cls.requests_map_trans
        cls.current = cls.requests_map_trans[request] = TransactionNode('root')

    @classmethod
    def stop(cls, request):
        if request in cls.requests_map_trans:
            del cls.requests_map_trans[request]
            if not len(cls.requests_map_trans):
                cls.current = None

    @classmethod
    def get_root(cls, request):
        return cls.requests_map_trans.get(request, None)

    @classmethod
    def set_current(cls, trans_node):
        cls.current = trans_node

    @classmethod
    def get_current(cls):
        return cls.current

    @classmethod
    def is_active(cls):
        return cls.current is not None


class SyncTransactionContext(object):

    node_cls = TransactionNode

    def __init__(self, full_name):
        self.full_name = full_name
        self.transaction = None

    def __enter__(self):
        if Transaction.is_active():
            self.parent = Transaction.current
            self.transaction = self.parent.children.get(self.full_name, self.node_cls(self.full_name))
            self.transaction.start()
            self.parent.children[self.full_name] = self.transaction
            Transaction.set_current(self.transaction)
            return self.transaction

    def __exit__(self, exc, value, tb):
        if Transaction.is_active():
            self.transaction.stop()
            Transaction.set_current(self.parent)


class AsyncTransactionContext(object):
    """
    装饰Runner.run时使用
    """
    def __init__(self, transaction):
        self.transaction = transaction

    def __enter__(self):
        if Transaction.is_active():
            self.parent = Transaction.current
            Transaction.set_current(self.transaction)
            self.transaction.resume()
            return self

    def __exit__(self, exc, value, tb):
        if Transaction.is_active():
            self.transaction.hang_up()
            Transaction.set_current(self.parent)


class AsyncCallbackContext(object):
    """
    gen.Task 执行callback时， 实际是进入了关联的Runner的run方法， 这部分代码执行时间不作为Task的时间
    """
    def __enter__(self):
        if Transaction.is_active():
            Transaction.current.stop()
            self.parent = Transaction.current
            return self

    def __exit__(self, exc, value, tb):
        if Transaction.is_active():
            self.parent.restart()
            Transaction.set_current(self.parent)

"""
Runner __init__ 时附加属性_td_transaction

Runner.run
   tempt_parent = Transaction.current
   Transaction.set_current(_td_transaction)
   _td_transaction.resume()
   run
   _td_transaction.hang_up()
   Transaction.set_current(tempt_parent)
"""
