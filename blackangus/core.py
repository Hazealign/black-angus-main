from pathlib import Path

from discord.ext import commands

from blackangus.config import Config, load


class BotCore:
    """
    흑우 봇의 코어 클래스
    """

    def __init__(self, config: str):
        self.config: Config = load(Path(config))
        self.bot = commands.Bot(command_prefix=self.config.bot.prefix)
        print(self.config)

    def run(self):
        self.bot.run(self.config.discord.token)
