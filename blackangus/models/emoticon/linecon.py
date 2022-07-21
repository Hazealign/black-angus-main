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


class LineconModel(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    line_id: int = Field(required=True)

    name: str = Field(required=True, min_length=1, max_length=10)

    title: str = Field(required=True, min_length=1)

    created_at: datetime = Field(default_factory=datetime.now)

    removed: bool = Field(default=False, required=False)
