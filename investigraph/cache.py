from functools import cache
from typing import Any

import fakeredis
import redis
import shortuuid
from cachelib.serializers import RedisSerializer

from investigraph import settings


class Cache:
    """
    This is an extremly simple cache interface for sharing tasks data
    efficiently via redis (or fakeredis during development)

    it creates (prefixed) random keys during data set to cache.

    it mimics redis GETDEL so that after fetching data from cache the key is
    deleted (turn of by `delete=False`)
    """

    serializer = RedisSerializer()

    def __init__(self):
        if settings.DEBUG:
            con = fakeredis.FakeStrictRedis()
        else:
            con = redis.from_url(settings.REDIS_URL)
        con.ping()
        self.cache = con

    def set(self, data: Any, key: str | None = None) -> str:
        data = self.serializer.dumps(data)
        key = key or shortuuid.uuid()
        self.cache.set(self.get_key(key), data)
        return key

    def get(self, key: str, delete: bool | None = True) -> Any:
        key = self.get_key(key)
        res = self.cache.get(key)
        if delete:
            self.cache.delete(key)  # GETDEL
        if res is not None:
            data = self.serializer.loads(res)
            return data

    @staticmethod
    def get_key(key: str) -> str:
        return f"{settings.CACHE_PREFIX}:{key}"


@cache
def get_cache() -> Cache:
    return Cache()
