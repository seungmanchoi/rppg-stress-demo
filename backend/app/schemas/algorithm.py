from typing import Literal

from pydantic import BaseModel, ConfigDict


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(w.title() for w in parts[1:])


class AlgorithmMetaOut(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)

    id: str
    display_name: str
    short_description: str
    type: Literal["unsupervised", "supervised"]
    backbone: str
    pretrained_on: str | None = None
    model_size_mb: int | None = None
