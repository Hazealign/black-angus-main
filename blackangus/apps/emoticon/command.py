import logging
from io import BytesIO
import shlex
import traceback
from typing import Optional, Dict, Any, Tuple

import discord
from discord import Embed, Client, Color, File

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.services.emoticon import RegionEnum
from blackangus.services.emoticon.linecon import LineconService
from blackangus.services.emoticon.main import EmoticonService


class EmoticonCommandApp(PresentedResponseApp):
    disabled = False
    commands = ['emoticon', '이모티콘']
    emoticon_service: EmoticonService
    linecon_service: LineconService

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client
        self.emoticon_service = EmoticonService(config.emoticon)
        self.linecon_service = LineconService(config.emoticon)

    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        def is_equivalents_option(x: str):
            return x in ['-e', '--equivalents']

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

        if parsed[0] in ['목록', 'list']:
            return {
                'help': False,
                'action': 'list',
                'channel_id': context.channel.id,
            }

        if parsed[0] in ['추가', 'add', 'create']:
            if len(parsed) < 3:
                return {'error': True}

            return {
                'help': False,
                'action': 'create',
                'keyword': parsed[1],
                'url': parsed[2],
            }

        if parsed[0] in ['검색', 'search']:
            if len(parsed) < 2:
                return {'error': True}

            return {
                'help': False,
                'action': 'search',
                'keyword': parsed[1],
            }

        if parsed[0] in ['복제', 'duplicate']:
            if len(parsed) < 3:
                return {'error': True}

            return {
                'help': False,
                'action': 'duplicate',
                'keyword': parsed[1],
                'target': parsed[2],
            }

        if parsed[0] in ['수정', 'edit', 'update']:
            if len(parsed) < 4:
                return {'error': True}

            first_equivalents = len(parsed) == 5 and is_equivalents_option(parsed[1])
            last_equivalents = len(parsed) == 5 and is_equivalents_option(parsed[3])

            change_elem = parsed[2] if first_equivalents else parsed[1]
            change = (
                'link'
                if change_elem in ['url', 'link', 'URL', '주소', '링크']
                else 'keyword'
            )

            return {
                'help': False,
                'action': 'update',
                'change': change,
                'keyword': parsed[3] if first_equivalents else parsed[2],
                'target': parsed[4] if first_equivalents else parsed[3],
                'equivalents': first_equivalents or last_equivalents,
            }

        if parsed[0] in ['삭제', 'delete', 'remove']:
            if len(parsed) < 2:
                return {'error': True}

            first_equivalents = len(parsed) == 3 and is_equivalents_option(parsed[1])
            last_equivalents = len(parsed) == 3 and is_equivalents_option(parsed[2])

            return {
                'help': False,
                'action': 'delete',
                'keyword': parsed[2] if first_equivalents else parsed[1],
                'equivalents': first_equivalents or last_equivalents,
            }

        if parsed[0] in ['라인-검색', '라인_검색', 'line-search', 'line_search']:
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
                'action': 'line-search',
                'keyword': keyword,
                'region': typed_region,
                'page': page,
                'limit': limit,
            }

        if parsed[0] in [
            '라인_추가',
            '라인-추가',
            '라인_등록',
            '라인-등록',
            'line_add',
            'line-add',
            'line_create',
            'line-create',
        ]:
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
                'action': 'line-create',
                'name': name,
                'line_id': line_id,
                'region': typed_region,
            }

        if parsed[0] in [
            '라인_삭제',
            '라인-삭제',
            'line_remove',
            'line-remove',
            'line_delete',
            'line-delete',
        ]:
            if len(parsed) < 2:
                return {'error': True}

            return {
                'help': False,
                'action': 'line-delete',
                'name': parsed[1],
            }

        if parsed[0] in ['라인_목록', '라인-목록', 'line_list', 'line-list']:
            return {
                'help': False,
                'action': 'line-list',
            }

        return {'help': True}

    @staticmethod
    def help_embed() -> Embed:
        return (
            Embed(
                title='흑우봇 이모티콘 사용법',
                description='웹, 라인, 디시인사이드 등에서 받은 이모티콘을 쓸 수 있습니다.',
                color=Color.light_gray(),
            )
            .add_field(
                name='호출',
                value='대화 중 이모티콘을 쓸 수 있습니다.\n`~이모티콘_이름`로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='새 이모티콘 추가(추가, add, create)',
                value='새 이모티콘을 웹에서 추가할 수 있습니다.\n' '`!이모티콘 추가 이름 URL`로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='이모티콘 전체 목록 보기(목록, list)',
                value='전체 이모티콘 목록(이름)을 가져옵니다.\n' '`!이모티콘 목록`으로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='이모티콘 검색하기(검색, search)',
                value='특정 단어가 들어간 이모티콘을 검색합니다.\n' '`!이모티콘 검색 이름`으로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='이모티콘 복제하기(복제, duplicate)',
                value='다른 단어로 같은 이모티콘을 복제할 수 있습니다.\n'
                '`!이모티콘 복제 이름 복제할_단어`로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='이모티콘 수정하기(수정, edit)',
                value='이모티콘의 이름 혹은 이미지를 교체할 수 있습니다.\n'
                '**이미지를 변경하면 해당 이모티콘에서 복제된 이모티콘은 반영되지 않는 것이 기본 동작입니다.**\n'
                '복제된 다른 이모티콘을 수정하지 않으려면 `-e`, `--equivalents` 옵션을 넣어주세요.\n'
                '`!이모티콘 수정 [-e] 주소 이모티콘_이름 새_URL`로 주소를 바꾸거나, \n'
                '`!이모티콘 수정 이름 이모티콘_이름 새_이름`으로 이름을 바꿀 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='이모티콘 삭제하기(삭제, remove, delete)',
                value='이모티콘을 삭제할 수 있습니다.\n'
                '실제로 내부에서 데이터베이스나 이미지가 삭제되지는 않습니다.\n'
                '**복제된 이모티콘은 반영되지 않는 것이 기본 동작입니다.**\n'
                '복제된 다른 이모티콘까지 삭제하려면 `-e`, `--equivalents` 옵션을 넣어주세요.\n'
                '`!이모티콘 삭제 [-e] 이름`으로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 이모티콘 검색(라인_검색, 라인-검색, line_search, line-search)',
                value='라인에서 이모티콘을 검색할 수 있습니다.\n'
                '리전은 `-r`, `--region` 옵션으로 넣을 수 있으며 옵션이 없으면 기본 도쿄에서 실행됩니다.\n'
                '`!이모티콘 라인-검색 [-r 리전] 검색어 [페이지 가져올_갯수]` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 이모티콘 일괄 추가(라인_추가, 라인-추가, line_add, line-add, line_create, line-create)',
                value='라인에서 한 상품의 이모티콘을 일괄적으로 추가합니다. 리전은 현재는 JP와 KR만 지원합니다.\n'
                '리전은 `-r`, `--region` 옵션으로 넣을 수 있으며 옵션이 없으면 기본 도쿄에서 실행됩니다.\n'
                '검색한 리전과 동일한 리전에서 실행하는 것을 강력히 권장합니다.\n'
                '이름은 10글자 이내로 입력해야합니다.\n'
                '`!이모티콘 라인-추가 [-r 리전] 이름 상품_ID` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 이모티콘 일괄 삭제(라인_삭제, 라인-삭제, line_remove, line-remove, line_delete, line-delete)',
                value='라인에서 한 상품의 이모티콘을 일괄적으로 삭제합니다.\n연결된 모든 이모티콘을 삭제하므로 주의가 필요합니다.\n'
                '`!이모티콘 라인-삭제 이름` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='라인 이모티콘 목록(라인_목록, 라인-목록, line_list, line-list)',
                value='라인으로 추가된 이모티콘 목록을 검색합니다.\n' '`!이모티콘 라인-목록` 명령어로 사용할 수 있습니다.',
                inline=False,
            )
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        logging.info('Presenting Emoticon Command: %s', command)

        if command.get('error', False):
            return None, Embed(
                title='흑우봇 이모티콘',
                description='명령어를 잘못 입력했습니다. `!emoticon --help`를 참고해주세요.',
                color=Color.red(),
            )

        if command.get('help', False):
            return None, self.help_embed()

        try:
            action = command['action']

            if action == 'list':
                emoticons_string = await self.emoticon_service.list_emoticons()
                emoticon_bytes = BytesIO('\n'.join(emoticons_string).encode('utf-8'))

                temp_file = File(emoticon_bytes, filename='emoticons.txt')

                channel = self.client.get_channel(command['channel_id'])
                await channel.send(
                    content=f'현재 등록된 이모티콘은 {len(emoticons_string)}개이며, 목록은 다음과 같습니다.',
                    file=temp_file,
                )

                return None, None

            if action == 'create':
                name = command['name']
                url = command['url']

                result = await self.emoticon_service.create(name, url)
                logging.info(f'Created: {result}')
                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'이모티콘을 성공적으로 추가했습니다.',
                    color=Color.green(),
                )

            if action == 'search':
                name = command['name']

                emoticons = await self.emoticon_service.search(name)
                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'{name} 키워드로 검색한 결과는 {len(emoticons)}건입니다.',
                    color=Color.green(),
                ).add_field(
                    name='목록',
                    value=', '.join(map(lambda x: f'`{x.name}`', emoticons)),
                    inline=False,
                )

            if action == 'duplicate':
                name = command['name']
                target = command['target']

                result = await self.emoticon_service.duplicate(name, target)
                logging.info(f'Duplicated: {result}')
                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'이모티콘을 성공적으로 복제했습니다.',
                    color=Color.green(),
                )

            if action == 'update':
                name = command['name']
                target = command['target']
                change = command['change']
                equivalents = command['equivalents']

                if change == 'link':
                    updated_value = await self.emoticon_service.update(
                        name, target, update_equivalents=equivalents
                    )
                else:
                    updated_value = await self.emoticon_service.rename(name, target)

                logging.info(f'Updated: {updated_value}')

                if type(updated_value) == list:
                    description = f'복제된 이모티콘을 포함해 총 {len(updated_value)}건이 업데이트되었습니다.'
                else:
                    description = '이모티콘이 성공적으로 업데이트되었습니다.'

                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=description,
                    color=Color.green(),
                )

            if action == 'delete':
                name = command['name']
                equivalents = command['equivalents']

                await self.emoticon_service.remove(name, remove_equivalents=equivalents)

                if equivalents:
                    description = '복제된 이모티콘을 포함해 이모티콘이 성공적으로 삭제되었습니다.'
                else:
                    description = '이모티콘이 성공적으로 삭제되었습니다.'

                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=description,
                    color=Color.green(),
                )

            if action == 'line-search':
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

            if action == 'line-create':
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

            if action == 'line-delete':
                name = command['name']
                await self.linecon_service.remove_item(name)
                return None, Embed(
                    title='흑우봇 이모티콘',
                    description=f'{name}과 관련된 라인 이모티콘들이 성공적으로 삭제되었습니다.',
                    color=Color.green(),
                )

            if action == 'line-list':
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
                title=f'흑우봇 이모티콘 오류: [{type(e)}]',
                description=f'다음과 같은 오류가 발생했습니다.\n{e}',
                color=Color.red(),
            )
