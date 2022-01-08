import pathlib
import sys
from typing import List

import toml
from pydantic import BaseModel, Field


class DiscordConfig(BaseModel):
    client_id: str
    client_secret: str
    public_key: str
    token: str


class BotConfig(BaseModel):
    app_list: List[str] = Field(default_factory=list)
    prefix: str = Field(default='!')
    log_when_ready: bool = Field(default=False)
    log_channel: str


class Config(BaseModel):
    discord: DiscordConfig
    bot: BotConfig


def panic(message: str, *args):
    print(message.format(*args), file=sys.stderr)
    raise SystemExit(1)


def load(path: pathlib.Path) -> Config:
    """지정한 Path에서 toml 파일을 serialize합니다."""
    if not path.exists() or not path.is_file() or not path.match('*.toml'):
        panic('지정한 경로에 파일이 없거나, 파일이 아니거나, toml 파일이 아닙니다.')

    try:
        return Config.parse_obj(toml.loads(path.read_text()))
    except TypeError as e:
        panic(str(e))
        raise
