import csv
import sys
from io import StringIO

import orjson

# from investigraph.logic import requests
import requests

from investigraph.model import Context

URL = "http://localhost:8000/all-authorities.csv"


def extract(ctx: Context, *args, **kwargs):
    res = requests.get(URL)
    reader = csv.DictReader(StringIO(res.text))
    yield from reader


def load(ctx, proxies, *args, **kwargs):
    for proxy in proxies:
        sys.stdout.write(orjson.dumps(proxy).decode())
        return
