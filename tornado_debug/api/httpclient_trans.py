# coding:utf8
import collections
from .transaction import TransactionNode

HttpRequest = collections.namedtuple('HttpRequest', ['url', 'code', 'time'])


class HttpClientTransNode(TransactionNode):
    urls_result = []

    @staticmethod
    def clear():
        HttpClientTransNode.urls_result = []

    @classmethod
    def add_request(cls, url, code, time):
        cls.urls_result.append(HttpRequest(url, code, time))

    @classmethod
    def get_result(cls):
        return cls.urls_result
