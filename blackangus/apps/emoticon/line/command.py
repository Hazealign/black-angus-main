import logging
import shlex
import traceback
from typing import Dict, Any, Tuple, Optional

from discord import Client, Embed, Message, Color
from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.services.emoticon import RegionEnum
from blackangus.services.emoticon.linecon import LineconService


class LineEmoticonCommandApp(PresentedResponseApp):
    disabled = False
    commands = ['line', 'linecon', '라인', '라인콘']
    linecon_service: LineconService

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client
        self.linecon_service = LineconService(config.emoticon)

    async def parse_command(self, context: Message) -> Optional[Dict[str, Any]]:
        def is_region_option(x: str):
            return x in ['-r', '--region']

        # noinspection PyTypeChecker
        parsed = shlex.split(context.clean_content)[1:]

        if (
            len(parsed) < 1
            or '-h' in parsed
            or '--help' in parsed
            or parsed[0] in ['도움', 'help']
        ):
            return {'help': True}

        if parsed[0] in ['검색', 'search']:
            if len(parsed) < 2:
                return {'error': True}

            has_region_first = len(parsed) > 4 and is_region_option(parsed[1])
            has_region_last = len(parsed) > 4 and is_region_option(parsed[-2])

            if has_region_first:
                region = parsed[2]
                keyword = parsed[3]
                page = 1 if len(parsed) < 6 else int(parsed[4])
                limit = 10 if len(parsed) < 6 else int(parsed[5])

            elif has_region_last:
                region = parsed[-1]
                keyword = parsed[1]
                page = 1 if len(parsed) < 6 else int(parsed[2])
                limit = 10 if len(parsed) < 6 else int(parsed[3])
            else:
                region = 'jp'
                keyword = parsed[1]
                page = 1 if len(parsed) < 3 else int(parsed[2])
                limit = 10 if len(parsed) < 3 else int(parsed[3])

            if region.lower() not in ['kr', 'jp']:
                return {'error': True}

            typed_region = RegionEnum[region.upper()]

            return {
                'help': False,
                'action': 'search',
                'keyword': keyword,
                'region': typed_region,
                'page': page,
                'limit': limit,
            }

        if parsed[0] in ['추가', '등록', 'add', 'create']:
            if len(parsed) < 3:
                return {'error': True}

            has_region_first = len(parsed) == 5 and is_region_option(parsed[1])
            has_region_last = len(parsed) == 5 and is_region_option(parsed[3])

            if has_region_first:
                if not parsed[3].isnumeric():
                    return {'error': True}

                region = parsed[2]
                line_id = int(parsed[4])
                name = parsed[3]
            elif has_region_last:
                if not parsed[2].isnumeric():
                    return {'error': True}

                region = parsed[4]
                line_id = int(parsed[2])
                name = parsed[1]
            else:
                region = 'jp'
                line_id = int(parsed[2])
                name = parsed[1]

            if region.lower() not in ['kr', 'jp']:
                return {'error': True}

            typed_region = RegionEnum[region.upper()]

            return {
                'help': False,
                'action': 'create',
                'name': name,
                '_id': line_id,
                'region': typed_region,
            }

        if parsed[0] in ['삭제', 'remove', 'delete']:
            if len(parsed) < 2:
                return {'error': True}

            return {
                'help': False,
                'action': 'delete',
                'name': parsed[1],
            }

        if parsed[0] in ['목록', 'list']:
            return {
                'help': False,
                'action': 'list',
            }

        return {'help': True}

    @staticmethod
    def help_embed() -> Embed:
        return (
            Embed(
                title='흑우봇 라인 이모티콘 기능',
                description='특정 라인 스티커 상품을 흑우봇에 가져와 이모티콘으로 쓸 수 있습니다.',
                color=Color.light_gray(),
            )
            .add_field(
                name='상품 검색(검색, search)',
                value='라인에서 상품 목록을 검색할 수 있습니다.\n'
                '리전은 `-r`, `--region` 옵션으로 `KR` 혹은 `JP`로 넣을 수 있으며 옵션이 없으면 기본 `JP`로 실행됩니다.\n'
                '`!라인콘 검색 [-r 리전] 검색어 [페이지 가져올_갯수]` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 상품 가져오기(추가, add, create)',
                value='라인에서 한 상품을 모두 가져와 이모티콘으로 추가합니다.\n'
                '리전은 `-r`, `--region` 옵션으로 `KR` 혹은 `JP`로 넣을 수 있으며 옵션이 없으면 기본 `JP`로 실행됩니다.\n'
                '검색한 리전과 동일한 리전에서 실행하는 것을 **강력히 권장**합니다.\n'
                '이름은 **10글자 이내**로 입력해야합니다.\n'
                '`!라인콘 추가 [-r 리전] 이름 상품_ID` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 상품 일괄 삭제(삭제, remove, delete)',
                value='라인에서 가져온 상품의 이모티콘을 일괄적으로 삭제합니다.\n연결된 모든 이모티콘을 삭제하므로 주의가 필요합니다.\n'
                '`!라인콘 삭제 이름` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='가져온 라인 상품 목록(목록, list)',
                value='라인에서 흑우봇으로 가져온 이모티콘 목록을 검색합니다.\n' '`!라인콘 목록` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        logging.info('Presenting Emoticon Command: %s', command)

        if command.get('error', False):
            return None, Embed(
                title='흑우봇 라인 이모티콘',
                description='명령어를 잘못 입력했습니다. `!라인콘 --help`를 참고해주세요.',
                color=Color.red(),
            )

        if command.get('help', False):
            return None, self.help_embed()

        try:
            action = command['action']

            if action == 'search':
                keyword = command['keyword']
                page = command['page']
                limit = command['limit']
                region = command['region']

                line_list = await self.linecon_service.search_list_from_server(
                    region=region,
                    keyword=keyword,
                    page=page,
                    limit=limit,
                )

                embed = Embed(
                    color=Color.green(),
                    title='흑우봇 이모티콘',
                    description=f'{keyword} 키워드로 검색한 결과는 {line_list.counts}건입니다.',
                )

                for item in line_list.items:
                    embed.add_field(
                        name=f'[{item.id}] {item.title}',
                        value=item.link,
                        inline=True,
                    )

                return None, embed

            if action == 'create':
                name = command['name']
                line_id = command['line_id']
                region = command['region']

                line_item = await self.linecon_service.fetch_item_from_server(
                    region=region,
                    linecon_id=line_id,
                )

                (linecon, emoticons) = await self.linecon_service.create_from_item(
                    name, line_item
                )

                emoticon_names = ', '.join(map(lambda x: f'`{x.name}`', emoticons))

                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'라인에서 이모티콘을 성공적으로 가져왔습니다. 가져온 이모티콘은 총 {len(emoticons)}건입니다.',
                    color=Color.green(),
                ).add_field(name='이모티콘 목록', value=emoticon_names, inline=False)

            if action == 'delete':
                name = command['name']
                await self.linecon_service.remove_item(name)
                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'{name}과 관련된 라인 이모티콘들이 성공적으로 삭제되었습니다.',
                    color=Color.green(),
                )

            if action == 'list':
                (linecons, dictionary) = await self.linecon_service.get_lists()

                embed = Embed(
                    color=Color.green(),
                    title='흑우봇 이모티콘',
                    description=f'총 {len(linecons)}개의 라인 상품이 등록되었습니다.',
                )

                for linecon in linecons:
                    emoticon_lists = ', '.join(
                        map(lambda x: f'`{x.name}`', dictionary[str(linecon.id)])
                    )

                    embed.add_field(
                        name=f'[{linecon.name}] {linecon.title}',
                        value=emoticon_lists,
                        inline=True,
                    )

                return None, embed

            return None, self.help_embed()
        except Exception as e:
            traceback.print_exc()
            return None, Embed(
                title=f'흑우봇 라인 이모티콘 오류: [{type(e)}]',
                description=f'다음과 같은 오류가 발생했습니다.\n{e}',
                color=Color.red(),
            )
