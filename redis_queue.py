# -*- coding: utf-8 -*-

import json
import hashlib
from redis import StrictRedis
from urllib import urlencode
import urlparse


class QueueManager(object):
    def __init__(self, host, port, auth, db=0, lock_key="lock_key", dup_key="dup_key"):
        self.redis_client = StrictRedis(host=host, port=port, password=auth, db=db)
        self.lock_key = lock_key
        self.dup_key = dup_key

    def queue_empty(self, queue_name):
        return self.queue_empty(queue_name) <= 0

    def queue_len(self, queue_name):
        return self.redis_client.llen(queue_name)

    @staticmethod
    def _encode_request(request):
        return json.dumps(request, encoding="utf-8")

    @staticmethod
    def _decode_request(encoded_request):
        return json.loads(encoded_request, encoding="utf-8")

    @staticmethod
    def get_full_url(request):
        request_url = request.get("url")
        parse_result = urlparse.urlparse(request_url)
        dict_query = dict(urlparse.parse_qsl(parse_result.query))
        params = request.get("params")
        if params:
            dict_query.update(params)
        if not dict_query:
            return request_url
        dict_query = dict(sorted(dict_query.iteritems(), key=lambda d: d[0]))
        str_query = urlencode(dict_query)
        return urlparse.urlunparse((parse_result.scheme, parse_result.netloc, parse_result.path, parse_result.params,
                                    str_query, parse_result.fragment))

    def finger_print(self, request):
        fp = hashlib.sha1()
        fp.update(request.get("method"))
        fp.update(self.get_full_url(request))
        return fp.hexdigest()

    def request_seen(self, request):
        fp = self.finger_print(request)
        added = self.redis_client.sadd(self.dup_key, fp)
        return added == 0

    def unique_lock(self, lock_key, lock_name="lock", expire=60):
        try:
            value = self.redis_client.setnx(lock_key, lock_name)
            if value:
                self.redis_client.expire(lock_key, expire)
                return True, "set unique lock successfully"
            else:
                return True, "unique lock still on"
        except Exception as e:
            return False, "set unique lock failed: %s" % str(e)

