from typing import Optional, Dict, Any, Tuple

from discord import Client, Message, Embed, Color

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.models.subscribe import RSSSubscriptionModel, RSSDocumentModel
from blackangus.utils.rss_feed import (
    fetch_rss_feed,
    struct_time_to_pendulum_datetime,
)


class RSSRegisterApp(PresentedResponseApp):
    disabled = False
    commands = ['구독', 'rss']

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client

    async def parse_command(self, context: Message) -> Optional[Dict[str, Any]]:
        parsed = context.clean_content.split(' ')[1:]

        if '--help' in parsed or '-h' in parsed:
            return {'help': True}

        return {
            'help': False,
            'name': parsed[0],
            'link': parsed[1],
            'channel': parsed[2].replace('#', ''),
            'guild_id': context.guild.id,
            'created_by': context.author.id,
        }

    @staticmethod
    def help_embed() -> Embed:
        return Embed(
            title='RSS 피드 구독',
            description='흑우로 RSS 피드를 특정 채널에 구독할 수 있습니다. '
            '`!rss 구독_이름 URL 채널`로 입력해주시면 등록이 가능합니다.',
            color=Color.green(),
        )

    @staticmethod
    def success_embed(name: str, channel: str) -> Embed:
        return Embed(
            title=f'[{name}] 구독 성공',
            description='요청하신 구독에 성공하셨습니다.\n'
            f'#{channel} 채널에 5~10분 정도 후부터 자동으로 새로운 글을 가져옵니다.',
            color=Color.green(),
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        if command['help']:
            return None, self.help_embed()

        subscription = RSSSubscriptionModel(
            created_by=command['created_by'],
            name=command['name'],
            link=command['link'],
            channel=command['channel'],
            guild_id=command['guild_id'],
        )

        try:
            rss_list = await fetch_rss_feed(command['link'])
            await subscription.insert()

            for entry in rss_list:
                document = RSSDocumentModel(
                    subscription_id=subscription.id,
                    title=entry.title,
                    link=entry.link,
                    author=entry.author,
                    description=entry.description,
                    published_at=struct_time_to_pendulum_datetime(
                        entry.published_parsed
                    ),
                )

                await document.insert()

                if (
                    not subscription.latest_published_at
                    or subscription.latest_published_at.timestamp()
                    < document.published_at.timestamp()
                ):
                    subscription.latest_published_at = document.published_at

            await subscription.replace()
            return None, self.success_embed(command['name'], command['channel'])
        except BaseException as e:
            return None, Embed(
                title=f'[{command["name"]}] 구독 실패',
                description=f'초기 RSS 피드를 가져올 수 없었기 때문에 구독에 실패하였습니다.\n{e}',
                color=Color.red(),
            )
