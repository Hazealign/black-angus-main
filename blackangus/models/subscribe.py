from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from beanie import Document
from pydantic import Field


class RSSSubscriptionModel(Document):
    # ID는 UUID로
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    # 생성 시점
    created_at: datetime = Field(default_factory=datetime.now)

    # 등록한 사람의 아이디
    created_by: int

    # 채널
    channel: str

    # 구독 이름
    name: str

    # 서버의 아이디
    guild_id: int

    # 구독할 RSS 피드
    link: str

    # 마지막 '업로드' 시간
    latest_published_at: Optional[datetime] = Field(default=None)


class RSSDocumentModel(Document):
    # ID는 UUID로
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    subscription_id: UUID

    # 글 제목
    title: str

    # 글 링크
    link: str

    # 글 작성자
    author: str

    # 글 프리뷰
    description: str

    # 작성일자
    published_at: datetime

    created_at: datetime = Field(default_factory=datetime.now)
