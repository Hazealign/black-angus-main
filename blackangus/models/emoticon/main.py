from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

import pymongo
from beanie import Document, Indexed
from pydantic import Field, BaseModel


# 이모티콘 출처를 새롭게 저장합니다.
class EmoticonFrom(Enum):
    WEB = 'web'
    LINE = 'line'
    DCINSIDE = 'dcinside'


# 기존 인공흑우 v1와 비슷하면서도 조금 더 간결해진 데이터 구조를 사용합니다.
class EmoticonModel(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    name: Indexed(typ=str, index_type=pymongo.TEXT, unique=False) = Field(  # type: ignore
        required=True, min_length=1, max_length=10
    )

    original_url: str = Field(required=True)

    image_path: str = Field(required=True)

    original_image_path: str = Field(required=False, default=None)

    image_from: EmoticonFrom = Field(default_factory=lambda: EmoticonFrom.WEB)

    # Line용 필드
    sound_url: str = Field(required=False, default=None)

    # LineconCategoryModel, DcconCategoryModel의 ID와 연결되는 기능
    relation_id: Optional[UUID] = Field(default=None)

    removed: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)

    migrated_from_v1: bool = Field(default=False, required=False)


class EmoticonListView(BaseModel):
    name: str
