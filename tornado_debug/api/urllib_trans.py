# coding:utf8
from .transaction import TransactionNode, SyncTransactionContext
from .utils import get_sorted_data


class UrllibTransNode(TransactionNode):
    requests_m_result = {}

    def classify(self, request):
        cls = UrllibTransNode
        node = self

        result = cls.requests_m_result.get(request, {})
        data = result.get(node.name, {'count': 0, 'time': 0})
        data['count'] += node.count
        data['time'] += node.time
        result[node.name] = data
        cls.requests_m_result[request] = result

    @classmethod
    def get_result(cls, request):
        if request not in cls.requests_m_result:
            return []
        return get_sorted_data(cls.requests_m_result[request])


class UrllibTransContext(SyncTransactionContext):
    node_cls = UrllibTransNode

    def __init__(self, url):
        full_name = "_tb_urllib_%s" % url
        return super(UrllibTransContext, self).__init__(full_name)
