from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from beanie import Document
from pydantic import Field


class AlarmModel(Document):
    # ID는 UUID로
    id: UUID = Field(default_factory=uuid4)  # type: ignore

    # 생성 시점
    created_at: datetime = Field(default_factory=datetime.now)

    # 등록한 사람의 아이디
    created_by: int

    # 채널
    channel_id: int

    # 알람 이름, 내용
    name: str
    content: str

    is_repeat: bool

    # 알람 시간
    time: Optional[datetime] = Field(default=None)
    crontab: Optional[str] = Field(default=None)

    # 마지막 작동한 시간
    last_activated_at: Optional[datetime] = Field(default=None)
    enabled: bool = Field(default=True)
