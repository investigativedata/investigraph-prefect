"""
aggregate fragments
"""

from uuid import uuid4

from ftmq.io import smart_read_proxies
from ftmstore import get_dataset

from investigraph.cache import get_cache
from investigraph.model import Context
from investigraph.settings import CHUNK_SIZE
from investigraph.types import CEGenerator


def get_smart_proxies(ctx: Context, uri: str) -> CEGenerator:
    """
    see if we have parts in cache during run time
    (mimics efficient globbing for remote sources)
    """
    cache = get_cache()
    uris = cache.smembers(ctx.make_cache_key(uri))
    if uris:
        for uri in uris:
            yield from smart_read_proxies(uri)
        return

    yield from smart_read_proxies(uri)


def in_memory(ctx: Context, in_uri: str) -> tuple[int, int]:
    """
    aggregate in memory: read fragments from `in_uri` and write aggregated
    proxies to `out_uri`

    as `smart_open` is used here, `in_uri` and `out_uri` can be any local or
    remote locations
    """
    ix = 0
    buffer = {}
    for ix, proxy in enumerate(get_smart_proxies(ctx, in_uri), 1):
        if ix % (CHUNK_SIZE * 10) == 0:
            ctx.log.info("reading in proxy %d ..." % ix)
        if proxy.id in buffer:
            buffer[proxy.id].merge(proxy)
        else:
            buffer[proxy.id] = proxy

    ctx.load_entities(buffer.values(), serialize=True)
    return ix, len(buffer.values())


def in_db(ctx: Context, in_uri: str) -> tuple[int, int]:
    """
    use ftm store database to aggregate.
    `in_uri`: database connection string
    """
    dataset = get_dataset("aggregate_%s" % uuid4().hex)
    bulk = dataset.bulk()
    for ix, proxy in enumerate(get_smart_proxies(ctx, in_uri)):
        if ix % 10_000 == 0:
            ctx.log.info("Write [%s]: %s entities", dataset.name, ix)
        bulk.put(proxy, fragment=str(ix))
    bulk.flush()
    proxies = []
    for ox, proxy in enumerate(dataset.iterate()):
        proxies.append(proxy)
        if ox % 10_000 == 0:
            ctx.load_entities(proxies, serialize=True)
            proxies = []
    ctx.load_entities(proxies, serialize=True)
    dataset.drop()
    return ix, ox
