from os import getenv
from pymemcache.client.base import PooledClient
from pymemcache import serde

CacheService = PooledClient(
    getenv('MEMCACHED_HOST', 'localhost:11211'),
    max_pool_size=8,
    serde=serde.pickle_serde
)
