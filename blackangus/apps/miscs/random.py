import random
from typing import Any, Dict, Optional, Tuple

import discord
from discord import Client, Embed

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config


class RandomApp(PresentedResponseApp):
    disabled = False
    commands = ['랜덤', 'random']

    def __init__(
        self,
        config: Config,
        client: Client,
    ):
        self.config = config
        self.client = client

    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        return {'list': context.clean_content.split(' ')[1:]}

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        target = command.get('list', None)
        if not target or len(target) == 0:
            return '선택지를 한 개 이상 입력해주세요.', None

        return f'랜덤 뽑기 결과는 [**{random.choice(target)}**]입니다.', None
