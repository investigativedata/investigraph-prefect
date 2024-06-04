"""
Cache remote file file fetching using `anystore`
"""

import random
import time
from functools import cache

import requests
from anystore import anycache, get_store
from anystore.settings import Settings
from anystore.store import BaseStore
from anystore.util import make_data_checksum

from investigraph.logging import get_logger
from investigraph.model.source import Source
from investigraph.settings import ANYSTORE_URI


@cache
def get_anystore() -> BaseStore:
    settings = Settings()
    settings.uri = ANYSTORE_URI
    return get_store(**settings.model_dump())


STORE = get_anystore()


def get_cache_key(url: str, *args, **kwargs) -> str | None:
    if kwargs.pop("stream", None) is True:
        return
    if not kwargs.pop("url_key_only", False):
        source = Source(uri=url)
        head = source.head()
        if head.ckey:
            return make_data_checksum((url, head.ckey, *args, kwargs))
    kwargs.pop("delay", None)
    kwargs.pop("stealthy", None)
    kwargs.pop("timeout", None)
    return make_data_checksum((url, *args, kwargs))


@anycache(key_func=get_cache_key, store=STORE)
def get(
    url: str,
    *args,
    url_key_only: bool | None = False,
    stealthy: bool | None = False,
    delay: int | None = None,
    **kwargs,
) -> requests.Response:
    if stealthy:
        kwargs["headers"] = kwargs.pop("headers", {})
        kwargs["headers"]["User-Agent"] = random.choice(AGENTS)
    if delay is not None:
        time.sleep(delay)
    kwargs["timeout"] = kwargs.pop("timeout", 30)
    log = get_logger(__name__)
    log.info(f"GET {url}")
    res = requests.get(url, *args, **kwargs)
    res.raise_for_status()
    return res


# https://www.useragents.me/#most-common-desktop-useragents-json-csv
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.4",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.10",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Geck",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.3",  # noqa: B950
]
