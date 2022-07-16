import logging
from typing import Optional, Dict, Any, Tuple

from discord import Client, Message, Embed, Color

from blackangus.apps.base import PresentedResponseApp
from blackangus.apps.search.base import parse_search_command
from blackangus.config import Config
from blackangus.models.search import YoutubeModel
from blackangus.scrapper.youtube import YoutubeScrapper


class YoutubeSearchApp(PresentedResponseApp):
    disabled = False
    commands = ['youtube', '유튜브']

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client

    async def parse_command(self, context: Message) -> Optional[Dict[str, Any]]:
        return await parse_search_command(context)

    @staticmethod
    def help_embed() -> Embed:
        return Embed(
            title='Youtube 검색',
            description='흑우로 유튜브 영상을 검색할 수 있습니다. API 방식이 아닌 스크래핑 방식을 이용하며, '
            '비-로그인 상태 웹에서 보는 것과 동일한 결과를 얻을 수 있습니다.\n'
            '사용법은 `!youtube --count=갯수 검색어`로 입력하면 되며, 10개 이하의 결과만 가져올 수 있습니다.',
            color=Color.red(),
        )

    @staticmethod
    def result_to_embed(model: YoutubeModel) -> Embed:
        logging.info(
            f'[YoutubeModel] {model.title} / {model.duration} / {model.uploader} / {model.link}'
        )
        return (
            Embed(
                title=f'{model.title}',
                description=f'{model.description}',
                color=Color.green(),
                url=model.link,
            )
            .set_image(url=model.thumbnail_link)
            .add_field(name='재생 시간', value=model.duration, inline=True)
            .add_field(name='업로더', value=model.uploader, inline=True)
        )

    @staticmethod
    def error_embed(error: Exception) -> Embed:
        return Embed(
            title='유튜브 검색 오류',
            description='유튜브 검색 중 오류가 발생했습니다.\n' f'{error}',
            color=Color.red(),
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        if command.get('help', False):
            return None, self.help_embed()

        keyword = command['keyword']
        scrapper = YoutubeScrapper()

        try:
            await scrapper.initialize()
            results = await scrapper.scrape(keyword, command['count'])
            await scrapper.finalize()

            if len(results) == 0:
                return '검색 결과가 없습니다.', None

            embeds = map(lambda result: self.result_to_embed(result), results)
            channel = self.client.get_channel(command['channel'])

            await channel.send(content='유튜브 검색 결과입니다.')
            for embed in embeds:
                await channel.send(embed=embed)
        except Exception as e:
            return None, self.error_embed(e)

        return None, None
