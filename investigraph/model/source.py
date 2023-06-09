from datetime import datetime
from typing import TypeAlias

import requests
from dateparser import parse as parse_date
from normality import slugify
from pantomime import normalize_mimetype
from pydantic import BaseModel

from investigraph.types import SDict
from investigraph.util import slugified_dict

TSourceHead: TypeAlias = "SourceHead"


class Source(BaseModel):
    name: str
    uri: str
    extract_kwargs: dict | None = {}

    def __init__(self, **data):
        data["name"] = data.get("name", slugify(data["uri"]))
        super().__init__(**data)

    def head(self) -> TSourceHead:
        res = requests.head(self.uri)
        return SourceHead(**self.dict(), **slugified_dict(res.headers))


class SourceHead(Source):
    etag: str | None = None
    last_modified: datetime | None = None
    content_type: str | None = None
    content_length: int | None = None

    def __init__(self, **data):
        super().__init__(
            last_modified=parse_date(data.pop("last_modified", "")),
            content_type=normalize_mimetype(data.pop("content_type", None)),
            **data,
        )

    @property
    def should_stream(self) -> bool:
        return self.content_length or 0 > 1024**3 * 5  # 5 MB


class SourceResponse(Source):
    is_stream: bool | None = False
    response: requests.Response
    header: SDict

    class Config:
        arbitrary_types_allowed = True

    @property
    def mimetype(self) -> str:
        return normalize_mimetype(self.header["content_type"])