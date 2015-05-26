# coding:utf8
import collections
from .transaction import TransactionNode, SyncTransactionContext

HttpRequest = collections.namedtuple('HttpRequest', ['url', 'code', 'time'])


class HttpClientTransNode(TransactionNode):
    requests_m_result = {}

    def __init__(self, name):
        self.private_requests = []
        return super(HttpClientTransNode, self).__init__(name)

    def add_request(self, url, code, time):
        self.private_requests.append(HttpRequest(url, code, time))

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
