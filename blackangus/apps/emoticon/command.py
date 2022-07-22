import logging
from io import BytesIO
import shlex
import traceback
from typing import Optional, Dict, Any, Tuple

import discord
from discord import Embed, Client, Color, File

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.services.emoticon.main import EmoticonService


class EmoticonCommandApp(PresentedResponseApp):
    disabled = False
    commands = ['emoticon', '이모티콘']
    emoticon_service: EmoticonService

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client
        self.emoticon_service = EmoticonService(config.emoticon)

    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        def is_equivalents_option(x: str):
            return x in ['-e', '--equivalents']

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
                'keyword': parsed[1].upper(),
                'url': parsed[2],
            }

        if parsed[0] in ['검색', 'search']:
            if len(parsed) < 2:
                return {'error': True}

            return {
                'help': False,
                'action': 'search',
                'keyword': parsed[1].upper(),
            }

        if parsed[0] in ['복제', 'duplicate']:
            if len(parsed) < 3:
                return {'error': True}

            return {
                'help': False,
                'action': 'duplicate',
                'keyword': parsed[1].upper(),
                'target': parsed[2].upper(),
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

            target = parsed[4] if first_equivalents else parsed[3]
            if change == 'keyword':
                target = target.upper()

            return {
                'help': False,
                'action': 'update',
                'change': change,
                'keyword': (parsed[3] if first_equivalents else parsed[2]).upper(),
                'target': target,
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
                'keyword': (parsed[2] if first_equivalents else parsed[1]).upper(),
                'equivalents': first_equivalents or last_equivalents,
            }

        return {'help': True}

    @staticmethod
    def help_embed() -> Embed:
        return (
            Embed(
                title='흑우봇 이모티콘 사용법',
                description='흑우봇에 등록된 모든 이모티콘을 관리할 수 있습니다.',
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
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        logging.info('Presenting Emoticon Command: %s', command)

        if command.get('error', False):
            return None, Embed(
                title='흑우봇 이모티콘',
                description='명령어를 잘못 입력했습니다. `!이모티콘 --help`를 참고해주세요.',
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
                name = command['keyword']

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

            return None, self.help_embed()
        except Exception as e:
            traceback.print_exc()
            return None, Embed(
                title=f'흑우봇 이모티콘 오류: [{type(e)}]',
                description=f'다음과 같은 오류가 발생했습니다.\n{e}',
                color=Color.red(),
            )
