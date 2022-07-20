from typing import Optional

import discord
from discord import Client, Embed, Color, File

from blackangus.apps.base import BaseResponseApp
from blackangus.config import Config
from blackangus.services.emoticon.main import EmoticonService


class EmoticonFetcherApp(BaseResponseApp):
    prefix: Optional[str] = None
    emoticon_service: EmoticonService

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client
        self.emoticon_service = EmoticonService(config.emoticon)

    async def action(self, context: discord.Message):
        prefix: str = self.prefix or self.config.bot.emoticon_prefix
        if not context.clean_content.startswith(prefix):
            return

        # 이모티콘 이름을 추출한다.
        emoticon_name = context.clean_content.split(' ')[0].replace(prefix, '')

        # 이모티콘을 찾는다.
        emoticon = await self.emoticon_service.find_by_name(emoticon_name)

        if emoticon is None:
            return await context.channel.send(
                embed=Embed(
                    title='흑우봇 이모티콘 찾기',
                    description=f'이모티콘 "{emoticon_name}"을 찾을 수 없습니다.',
                    color=Color.red(),
                )
            )

        # 파일을 보낸다.
        (file_name, file) = self.emoticon_service.download(emoticon)
        await context.channel.send(
            file=File(
                file,
                filename=file_name,
            )
        )
