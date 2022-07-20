import asyncio
import logging
from pathlib import Path
from typing import List

import discord
from aiocron import crontab
from beanie import init_beanie
from discord.ext import commands
import motor.motor_asyncio

from blackangus.apps.alarm.periodic import AlarmPeriodicApp
from blackangus.apps.alarm.register import AlarmCommandApp
from blackangus.apps.base import BasePeriodicApp, BaseResponseApp
from blackangus.apps.emoticon.command import EmoticonCommandApp
from blackangus.apps.emoticon.fetcher import EmoticonFetcherApp
from blackangus.apps.miscs.direction import NaverTransitDirectionApp
from blackangus.apps.miscs.random import RandomApp
from blackangus.apps.miscs.translation import TranslationApp
from blackangus.apps.miscs.weather import WeatherApp
from blackangus.apps.search.image import GoogleImageSearchApp
from blackangus.apps.search.youtube import YoutubeSearchApp
from blackangus.apps.subscription.periodic import RSSSubscriberApp
from blackangus.apps.subscription.register import RSSRegisterApp
from blackangus.config import Config, load
from blackangus.models.alarm import AlarmModel
from blackangus.models.emoticon.linecon import LineconModel, LineconCategoryModel
from blackangus.models.emoticon.main import EmoticonModel
from blackangus.models.subscribe import RSSDocumentModel, RSSSubscriptionModel


class BotCore:
    """
    흑우 봇을 실행할 수 있게 해주는 클래스
    """

    def __init__(self, config: str):
        self.logger = logging.getLogger('blackangus:core')
        self.config: Config = load(Path(config))
        self.bot = commands.Bot(command_prefix=self.config.bot.prefix)

        self.response_apps: List[BaseResponseApp] = [
            # 여기에 개발한 응답형 커맨드(앱)들을 넣어주세요.
            RandomApp(self.config, self.bot),
            TranslationApp(self.config, self.bot),
            WeatherApp(self.config, self.bot),
            RSSRegisterApp(self.config, self.bot),
            YoutubeSearchApp(self.config, self.bot),
            GoogleImageSearchApp(self.config, self.bot),
            NaverTransitDirectionApp(self.config, self.bot),
            AlarmCommandApp(self.config, self.bot),
            EmoticonFetcherApp(self.config, self.bot),
            EmoticonCommandApp(self.config, self.bot),
        ]

        self.periodic_apps: List[BasePeriodicApp] = [
            # 여기에 개발한 주기적 커맨드(앱)들을 넣어주세요.
            RSSSubscriberApp(self.config, self.bot),
            AlarmPeriodicApp(self.config, self.bot),
        ]

    def run(self):
        self.bot.event(self.on_message)
        self.bot.event(self.on_ready)

        for app in self.periodic_apps:
            crontab(app.period, func=app.action, start=True)

        self.bot.run(self.config.discord.token)

    async def on_message(self, context: discord.Message):
        if context.author.bot:
            return

        user_name = (
            context.author.name if context.author.nick is None else context.author.nick
        )

        self.logger.info(
            f'[{context.guild.name} - {context.channel.name}] '
            f'{user_name}: {context.clean_content}'
        )

        await asyncio.gather(*map(lambda x: x.action(context), self.response_apps))

    async def on_ready(self):
        # 봇이 준비되자마자 데이터베이스 연결을 한다.
        # run을 async로 만드는 것보다 이게 나음.
        client = motor.motor_asyncio.AsyncIOMotorClient(self.config.mongodb.url)

        await init_beanie(
            database=client[self.config.mongodb.database_name],
            document_models=[
                # 여기에 관련된 MongoDB 모델들을 넣어주세요.
                RSSDocumentModel,
                RSSSubscriptionModel,
                AlarmModel,
                EmoticonModel,
                LineconModel,
                LineconCategoryModel,
            ],
        )

        self.logger.info('봇이 준비되었습니다.')

        if not self.config.bot.log_when_ready:
            return

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.name.__contains__(self.config.bot.log_channel):
                    await channel.send('봇이 준비되었습니다.')
