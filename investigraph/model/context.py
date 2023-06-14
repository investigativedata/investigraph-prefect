from datetime import datetime

import orjson
import shortuuid
from followthemoney.util import make_entity_id
from nomenklatura.entity import CE
from nomenklatura.util import datetime_iso
from prefect.runtime import flow_run
from pydantic import BaseModel
from smart_open import open
from zavod.util import join_slug

from investigraph.cache import Cache, get_cache
from investigraph.logic.load import Loader, get_loader
from investigraph.settings import DATA_ROOT
from investigraph.util import ensure_path, make_proxy

from .config import Config
from .source import Source


class Context(BaseModel):
    dataset: str
    prefix: str
    config: Config
    source: Source
    run_id: str
    entities_loader: Loader
    fragments_loader: Loader

    class Config:
        arbitrary_types_allowed = True

    @property
    def cache(self) -> Cache:
        return get_cache()

    def export_metadata(self) -> None:
        data = self.config.metadata
        data["updated_at"] = data.get("updated_at", datetime_iso(datetime.utcnow()))
        data = orjson.dumps(data)
        with open(self.config.index_uri, "wb") as fh:
            fh.write(data)

    def make_proxy(self, *args, **kwargs) -> CE:
        return make_proxy(*args, **kwargs)

    def make_slug(self, *args, **kwargs) -> str:
        prefix = kwargs.pop("prefix", self.prefix)
        return join_slug(*args, prefix=prefix, **kwargs)

    def make_id(self, *args, **kwargs) -> str:
        prefix = kwargs.pop("prefix", self.prefix)
        return join_slug(make_entity_id(*args), prefix=prefix)


def init_context(config: Config, source: Source) -> Context:
    run_id = flow_run.get_id() or f"dummy-{shortuuid.uuid()}"
    path = ensure_path(DATA_ROOT / config.dataset)
    if config.index_uri is None:
        config.index_uri = (path / "index.json").as_uri()
    if config.fragments_uri is None:
        config.fragments_uri = (path / f"fragments.{run_id}.json").as_uri()
    if config.entities_uri is None:
        config.entities_uri = (path / "entities.ftm.json").as_uri()

    return Context(
        dataset=config.dataset,
        prefix=config.metadata.get("prefix", config.dataset),
        config=config,
        source=source,
        run_id=run_id,
        fragments_loader=get_loader(config.fragments_uri, config.dataset, parts=True),
        entities_loader=get_loader(config.entities_uri, config.dataset),
    )
