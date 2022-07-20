import dataclasses
from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field


@dataclasses.dataclass
class SearchResultModel:
    title: str
    id: int
    link: str


class LineconCategoryModel(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    originId: int = Field(required=True)

    name: str = Field(required=True, min_length=1, max_length=10)

    title: str = Field(required=True, min_length=1)

    path: str = Field(required=True)

    created_at: datetime = Field(default_factory=datetime.now)


class LineconModel(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    categoryId: UUID = Field(required=True)

    name: str = Field(required=True)

    thumbnail_path: str = Field(required=True)

    full_path: str = Field(required=True)

    animated: bool = Field(default=False)
