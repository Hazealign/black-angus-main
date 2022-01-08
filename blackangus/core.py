import logging
from pathlib import Path

import discord
from discord.ext import commands

from blackangus.config import Config, load


class BotCore:
    """
    흑우 봇을 실행할 수 있게 해주는 클래스
    """

    def __init__(self, config: str):
        self.logger = logging.getLogger('blackangus:core')
        self.config: Config = load(Path(config))
        self.bot = commands.Bot(command_prefix=self.config.bot.prefix)

    def run(self):
        self.bot.event(self.on_message)
        self.bot.event(self.on_ready)
        self.bot.run(self.config.discord.token)

    async def on_message(self, context: discord.Message):
        pass

    async def on_ready(self):
        self.logger.info('봇이 준비되었습니다.')

        if not self.config.bot.log_when_ready:
            return

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.name.__contains__(self.config.bot.log_channel):
                    await channel.send('봇이 준비되었습니다.')
