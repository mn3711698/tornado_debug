# coding:utf8
from .transaction import TransactionNode, SyncTransactionContext
from .utils import get_sorted_data


class UrllibTransNode(TransactionNode):
    urls_result = {}

    @staticmethod
    def clear():
        UrllibTransNode.urls_result = {}

    def classify(self):
        cls = UrllibTransNode
        node = self

        data = cls.urls_result.get(node.name, {'count': 0, 'time': 0})
        cls.urls_result[node.name] = data
        data['count'] += node.count
        data['time'] += node.time

    @classmethod
    def get_result(cls):
        cls.urls_result = get_sorted_data(cls.urls_result)
        return cls.urls_result


class UrllibTransContext(SyncTransactionContext):
    node_cls = UrllibTransNode

    def __init__(self, url):
        full_name = "_tb_urllib_%s" % url
        return super(UrllibTransContext, self).__init__(full_name)
