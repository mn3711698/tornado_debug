# coding: utf8
import time


class TransactionNode(object):
    """
    一次函数调用只使用一次start , stop
    对于异步函数，start , stop 之间有多次resume, 和 hangup
    """

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


class Transaction(object):

    current = root = TransactionNode('root')  # Transaction.root始终是单例

    active = True  # 标记当前的统计是否有效

    @classmethod
    def _clear(cls):
        cls.root.children = {}
        cls.current = cls.root

    @classmethod
    def start(cls):
        cls.active = True
        cls._clear()

    @classmethod
    def stop(cls):
        cls.active = False
        cls._clear()

    @classmethod
    def get_current(cls):
        return cls.current

    @classmethod
    def set_current(cls, transaction):
        cls.current = transaction


class SyncTransactionContext(object):

    def __init__(self, full_name):
        self.full_name = full_name
        self.transaction = None

    def __enter__(self):
        if Transaction.active:
            self.parent = Transaction.current
            self.transaction = self.parent.children.get(self.full_name, TransactionNode(self.full_name))
            self.transaction.start()
            self.parent.children[self.full_name] = self.transaction
            Transaction.set_current(self.transaction)
            return self.transaction

    def __exit__(self, exc, value, tb):
        if Transaction.active:
            self.transaction.stop()
            Transaction.set_current(self.parent)


class AsyncTransactionContext(object):
    """
    装饰Runner.run时使用
    """
    def __init__(self, transaction):
        self.transaction = transaction

    def __enter__(self):
        if Transaction.active:
            self.parent = Transaction.current
            Transaction.set_current(self.transaction)
            self.transaction.resume()
            return self

    def __exit__(self, exc, value, tb):
        if Transaction.active:
            self.transaction.hang_up()
            Transaction.set_current(self.parent)


class AsyncCallbackContext(object):
    """
    gen.Task 执行callback时， 实际是进入了关联的Runner的run方法， 这部分代码执行时间不作为Task的时间
    """
    def __enter__(self):
        if Transaction.active:
            Transaction.current.stop()
            self.parent = Transaction.current
            return self

    def __exit__(self, exc, value, tb):
        if Transaction.active:
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
