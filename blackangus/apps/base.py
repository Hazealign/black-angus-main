from abc import ABCMeta, abstractmethod
from typing import Optional, List, Tuple, Dict, Any

import discord
from discord import Embed, Client

from blackangus.config import Config


class AppException(Exception):
    pass


class BaseResponseApp(metaclass=ABCMeta):
    # 비활성화 플래그
    disabled: bool = False
    prefix: Optional[str] = None
    # 커맨드
    commands: List[str] = []

    config: Config
    client: Client

    @abstractmethod
    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def present(self, command: Dict[str, Any]) -> Tuple[Optional[str], Optional[Embed]]:
        pass

    async def action(self, context: discord.Message):
        # 플래그로 비활성화
        if self.disabled:
            return

        # 키워드랑 prefix로 조합하기
        prefix: str = self.prefix or self.config.bot.prefix
        if not any(map(
                lambda x: context.clean_content.startswith(f'{prefix}{x}'),
                self.commands
        )):
            return

        # parse, presenter, send
        command = await self.parse_command(context)
        if not command:
            return

        (content, embed) = await self.present(command)
        if content is not None or embed is not None:
            await context.channel.send(content=content, embed=embed)
