# coding:utf8
import json
from time import time

import redis

from tornado_debug.config import URL_PREFIX, REDIS_HOST, REDIS_PORT


client = redis.StrictRedis(REDIS_HOST, REDIS_PORT)


class CollectedData(object):
    @staticmethod
    def save(body):
        data = json.loads(body)
        response = data.get('response', {})
        if not response:
            return False
        url = response['content']['url']
        url_prefix = "/"
        for prefix in URL_PREFIX:
            if url.startswith(prefix):
                url_prefix = prefix
                break
        start_time = response['content']['start_time']
        time_use = response['content']['time_use']
        id = client.incr('debug:id')
        ex_seconds = 24*3600
        last_time = time() - ex_seconds

        info = "%s#%s" % (time_use, url)
        with client.pipeline() as pipeline:
            pipeline.zadd("url:%s" % url_prefix, start_time, id)
            pipeline.zremrangebyscore("url:%s" % url_prefix, -1, last_time)
            pipeline.set('info:%s' % id, info, ex_seconds)
            pipeline.set('data:%s' % id, body, ex_seconds)
            pipeline.execute()
        return True

    @staticmethod
    def get_info_list(seconds_ago):
        max_time = time()
        min_time = time() - seconds_ago
        url_keys = client.keys('url:*')
        result = {}
        for key in url_keys:
            ids_scores = client.zrangebyscore(key, min_time, max_time, withscores=True)
            info_keys = ["info:%s" % id for id, _ in ids_scores]
            if not info_keys:
                continue
            infos = client.mget(info_keys)
            times_urls = [info.split('#', 1) if info else info for info in infos]

            infos = []
            for id_score, time_url in zip(ids_scores, times_urls):
                if not time_url:
                    continue
                info = dict(
                    id=id_score[0],
                    start_time=id_score[1],
                    time_use=time_url[0],
                    url=time_url[1]
                )
                infos.append(info)
            result[key] = infos
        return result

    @staticmethod
    def get_detail(id):
        data = client.get("data:%s" % id)
        if not data:
            return {}
        return json.loads(data)
