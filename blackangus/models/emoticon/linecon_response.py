import dataclasses
from typing import Optional, List


@dataclasses.dataclass(frozen=True)
class LineconCategoryModel:
    title: str
    id: int
    link: str


@dataclasses.dataclass(frozen=True)
class LineconItemModel:
    type: str
    item_id: str
    url: str
    sound_url: Optional[str]


@dataclasses.dataclass(frozen=True)
class LineconCategoryDetailModel:
    item_id: int
    title: str
    description: str
    author: str
    items: List[LineconItemModel]


@dataclasses.dataclass(frozen=True)
class LineconCategoryListModel:
    counts: int
    items: List[LineconCategoryModel]
