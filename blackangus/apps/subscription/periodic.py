import logging
from time import mktime

import discord
import pendulum
from discord import Client, Embed
from html2text import HTML2Text

from blackangus.apps.base import BasePeriodicApp
from blackangus.config import Config
from blackangus.models.subscribe import RSSSubscriptionModel, RSSDocumentModel
from blackangus.utils.rss_feed import fetch_rss_feed, struct_time_to_pendulum_datetime


class RSSSubscriberApp(BasePeriodicApp):
    period = '*/2 * * * *'
    disabled = False

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client

    @staticmethod
    def make_embed_for_document(
        subscription: RSSSubscriptionModel, document: RSSDocumentModel
    ) -> Embed:
        html2text = HTML2Text()

        return Embed(
            title=f'[{subscription.name}] {document.title}',
            description=str.strip(html2text.handle(document.description)),
            url=document.link,
        ).set_footer(text='인공흑우가 구독한 글입니다.')

    async def action(self):
        subscriptions = await RSSSubscriptionModel.find(sort='created_at').to_list()

        for subscription in subscriptions:
            # 1. 새로운 피드가 있는지 가져온다.
            new_feeds = await fetch_rss_feed(
                subscription.link,
                pendulum.instance(subscription.latest_published_at)
                if subscription.latest_published_at
                else None,
            )

            if len(new_feeds) == 0:
                logging.info(f'{subscription.name} 구독에 새 피드가 없습니다.')
                continue

            # 2. 새로운 피드를 정렬하고 업데이트한다.
            new_feeds.sort(key=lambda f: mktime(f.published_parsed), reverse=False)

            for feed in new_feeds:
                document = RSSDocumentModel(
                    subscription_id=subscription.id,
                    title=feed.title,
                    link=feed.link,
                    author=feed.author,
                    description=feed.description,
                    published_at=struct_time_to_pendulum_datetime(
                        feed.published_parsed
                    ),
                )

                await document.insert()

                # Discord에 업로드한다.
                for guild in self.client.guilds:
                    if guild.id == subscription.guild_id:
                        channel = discord.utils.get(
                            guild.channels, name=subscription.channel
                        )

                        logging.info(f'Sending RSS to {subscription.channel}')

                        # 채널이 있으면 채널에 쏘세요!
                        if channel is not None:
                            await channel.send(
                                embed=self.make_embed_for_document(
                                    subscription, document
                                )
                            )

                # 마지막 업로드 시잔을 업데이트해준다.
                if (
                    not subscription.latest_published_at
                    or subscription.latest_published_at.timestamp()
                    < document.published_at.timestamp()
                ):
                    subscription.latest_published_at = document.published_at

            # 꼭 DB 객체도 update해줘야 한다.
            await subscription.replace()

        logging.info(f'RSS 피드 {len(subscriptions)}개 업데이트 완료.')
