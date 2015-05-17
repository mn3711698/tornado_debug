# coding: utf8
import time


class TransactionNode(object):
    """
    一次函数调用只使用一次start , stop
    start , stop 之间有多次resume, 和 hangup
    """

    def __init__(self, name):
        self.count = 0
        self.running = False
        self.time = 0
        self.name = name
        self.children = {}
        self.start_time = 0

    def start(self):
        self.running = True
        self.count += 1

    def stop(self):
        if self.start_time:
            self.hang_up()
        self.running = False

    def resume(self):
        self.running = True
        self.start_time = time.time()

    def hang_up(self):
        self.running = False
        self.time += (time.time() - float(self.start_time))
        self.start_time = 0

    def is_running(self):
        return self.running


class Transaction(object):

    parent = current = root = {}

    def __init__(self, full_name):
        self.full_name = full_name
        self.transaction = None

    @classmethod
    def clear(cls):
        cls.current = cls.root = {}

    @classmethod
    def get_current(cls):
        return cls.current

    @classmethod
    def set_current(cls, transaction):
        cls.current = transaction

    def __enter__(self):
        self.parent = self.current
        self.transaction = self.parent.children.get(self.full_name, TransactionNode(self.full_name))
        self.transaction.start()
        self.parent.children[self.full_name] = self.transaction
        self.set_current(self.transaction)
        return self.transaction

    def __exit__(self, exc, value, tb):
        self.transaction.stop()
        self.set_current(self.parent)


class AsyncTransaction(Transaction):
    """
    装饰Runner
    """
    def __init__(self, transaction):
        self.transaction = transaction

    def __enter__(self):
        if self.transaction != self.current:
            self.parent = self.current
        self.set_current(self.transaction)
        self.transaction.resume()
        return self

    def __exit__(self, exc, value, tb):
        self.transaction.hang_up()
        self.set_current(self.parent)
