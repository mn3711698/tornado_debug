# coding:utf8
from .transaction import TransactionNode, SyncTransactionContext


class HttpClientTransNode(TransactionNode):
    requests_m_result = {}

    def __init__(self, name):
        self.private_requests = []
        return super(HttpClientTransNode, self).__init__(name)

    def add_request(self, url, code, time):
        self.private_requests.append(dict(url=url, code=code, time=time))

    def classify(self, request):
        cls = HttpClientTransNode
        result = cls.requests_m_result.get(request, [])
        result.extend(self.private_requests)
        cls.requests_m_result[request] = result

    @classmethod
    def get_result(cls, request):
        return cls.requests_m_result.get(request, [])


class HttpClientTransContext(SyncTransactionContext):
    node_cls = HttpClientTransNode
