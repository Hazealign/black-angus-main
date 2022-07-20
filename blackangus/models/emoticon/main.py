from uuid import UUID, uuid4
from datetime import datetime
from typing import List

from beanie import Document, Indexed
from pydantic import Field


# 기존 인공흑우 v1와 비슷하면서도 조금 더 간결해진 데이터 구조를 사용합니다.
class EmoticonModel(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    name: str = Indexed(Field(required=True, min_length=1, max_length=10))

    equivalents: List[str] = Field(default_factory=list)

    path: str = Field(equired=True)

    removed: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)
