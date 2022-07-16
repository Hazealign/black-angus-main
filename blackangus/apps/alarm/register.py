import shlex
from typing import Dict, Any, Tuple, Optional

import discord
import pendulum
from discord import Client, Embed, Message, Color
from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.models.alarm import AlarmModel
from blackangus.utils.crontab import get_next_crontab_time


class AlarmCommandApp(PresentedResponseApp):
    disabled = False
    commands = ['alarm', '알람']

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client

    async def parse_command(self, context: Message) -> Optional[Dict[str, Any]]:
        # noinspection PyTypeChecker
        parsed = shlex.split(context.clean_content)[1:]

        if len(parsed) <= 1:
            return {'help': True}

        try:
            if parsed[0] == 'help' or '-h' in parsed or '--help' in parsed:
                return {'help': True}

            # 등록 커맨드
            elif parsed[0] == 'register' or parsed[0] == '등록':
                if len(parsed) < 5:
                    return {'error': True}

                # 채널이 없으면 기본임
                if '--channel' in parsed:
                    channel_name = parsed[parsed.index('--channel') + 1].replace(
                        '#', ''
                    )
                    channel_id = discord.utils.get(
                        self.client.get_all_channels(), name=channel_name
                    )
                    if channel_id is None:
                        return {'error': True}
                else:
                    channel_id = context.channel.id

                # 이름 반복/일회 시간/crontab 순서임
                do_repeat = '반복' == parsed[3] or 'repeat' == parsed[3]

                return {
                    'help': False,
                    'command': 'register',
                    'user_id': context.author.id,
                    'channel_id': channel_id,
                    'name': parsed[1],
                    'content': parsed[2],
                    'repeat': do_repeat,
                    # 시간을 파싱하거나, 아니면 Crontab을 받습니다.
                    'time': pendulum.parse(parsed[4], tz='Asia/Seoul')
                    if not do_repeat
                    else parsed[4],
                }

            # 삭제 커맨드, 등록한 사람만 삭제할 수 있음.
            elif parsed[0] == 'unregister' or parsed[0] == '삭제':
                if len(parsed) < 2:
                    return {'error': True}

                return {
                    'help': False,
                    'command': 'unregister',
                    'user_id': context.author.id,
                    'name': parsed[1],
                }

            # 내 목록 커맨드
            elif parsed[0] == 'list' or parsed[0] == '목록':
                return {
                    'help': False,
                    'command': 'list',
                    'user_id': context.author.id,
                }
        except Exception as e:
            return {'error': True, 'exception': e}

        return {'help': True}

    @staticmethod
    def help_embed() -> Embed:
        return (
            Embed(
                title='알람 설정',
                description='흑우로 1회용, 다회용 알람을 설정할 수 있습니다.\n'
                'alarm, 알람 키워드로 사용할 수 있습니다.',
                color=Color.green(),
            )
            .add_field(
                name='register / 등록',
                value='알람을 새로 등록합니다.'
                '`!알람 등록 이름 내용 1회/반복 시간 [--channel #채널_이름]` 형태로 사용할 수 있습니다.\n'
                '시간은 1회성 알람일 경우 **`2022-00-00 12:34:00`**과 같이 입력해주세요. **초 단위는 무시됩니다.**\n'
                '반복성 알람인 경우, crontab 문자열을 사용해야합니다. '
                '예를 들어 매일 오후 6시 반에 알람을 받으려면 `30 18 * * *`이라고 입력해주세요.\n'
                '매일 아침 7시 15분이라면 `15 7 * * *`이 될 것입니다.\n'
                '분 시 날짜 월 요일(숫자) 순으로 되어있으며, wildcard 등을 지원합니다. '
                '자세한 내용은 https://crontab.guru 를 방문해서 참고해주세요.',
                inline=False,
            )
            .add_field(
                name='unregister / 삭제',
                value='**내가 등록한 알람**만 해제할 수 있습니다.\n' '`!알람 삭제 이름`으로 삭제할 수 있습니다.',
                inline=False,
            )
            .add_field(
                name='list / 목록', value='내가 등록한, 활성화된 알람 목록을 가져올 수 있습니다.', inline=False
            )
        )

    @staticmethod
    async def register(command: Dict[str, Any]) -> Embed:
        prev_alarms = await AlarmModel.find(
            {
                'user_id': command['user_id'],
                'name': command['name'],
                'enabled': True,
            },
            limit=1,
        ).to_list()

        if len(prev_alarms) != 0:
            return Embed(
                color=Color.red(),
                title='알람 등록 실패',
                description='이미 등록한 알람이 있습니다.',
            )

        alarm = AlarmModel(
            created_by=command['user_id'],
            channel_id=command['channel_id'],
            name=command['name'],
            content=command['content'],
            is_repeat=command['repeat'],
        )

        if command['repeat']:
            alarm.crontab = command['time']
            alarm.time = get_next_crontab_time(
                pendulum.now(tz='Asia/Seoul'), command['time']
            )
        else:
            if type(command['time']) is not pendulum.DateTime or command[
                'time'
            ] <= pendulum.now(tz='Asia/Seoul'):
                return Embed(
                    color=Color.red(),
                    title='알람 등록 실패',
                    description=f'과거를 대상으로 알람을 등록할 수 없습니다, {type(command["time"])}',
                )
            alarm.time = command['time']

        # 만들었으면 저장해야지.
        await alarm.create()
        return Embed(
            color=Color.green(),
            title='알람 등록 완료',
            description=f'[{alarm.name}] 알람이 등록 완료되었습니다.',
        )

    @staticmethod
    async def unregister(command: Dict[str, Any]) -> Embed:
        alarm = await AlarmModel.find(
            {
                'user_id': command['user_id'],
                'name': command['name'],
                'enabled': True,
            },
            limit=1,
        ).to_list()

        if len(alarm) == 0:
            return Embed(
                color=Color.red(),
                title='알람 삭제 실패',
                description='해당 사용자가 해당 이름으로 등록한 알람이 없습니다.',
            )

        await alarm[0].delete()
        return Embed(
            color=Color.green(),
            title='알람 삭제 완료',
            description='해당 알람을 삭제했습니다.',
        )

    @staticmethod
    async def list(command: Dict[str, Any]) -> Embed:
        alarms = await AlarmModel.find(
            {
                'user_id': command['user_id'],
                'enabled': True,
            }
        ).to_list()

        if len(alarms) == 0:
            return Embed(
                color=Color.green(),
                title='알람 목록 조회',
                description='해당 사용자가 등록한 알람이 없습니다.',
            )

        embed = Embed(
            color=Color.green(),
            title='알람 목록 조회',
            description='해당 사용자가 등록한 알람은 다음과 같습니다.',
        )

        for alarm in alarms:
            text = (
                f'반복 알람: {alarm.crontab}'
                if not alarm.is_repeat
                else f'일회성 알람: {pendulum.instance(alarm.time, tz="Asia/Seoul").to_datetime_string()}'  # type: ignore
            )
            embed = embed.add_field(name=alarm.name, value=text, inline=False)

        return embed

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        if command.get('error', False):
            embed = Embed(
                title='알람 옵션 오류',
                description='알람 커맨드의 사용법을 확인해주세요. 이 문제는 주로 제대로 커맨드를 입력하지 않았거나,'
                ' 등록한 채널이 정확하지 않으면 발생합니다.',
                color=Color.red(),
            )

            # 익셉션 로그가 있으면 보여줘야지...
            if command.get('exception', None) is not None:
                embed = embed.add_field(
                    name='오류 내용', value=str(command['exception']), inline=False
                )

            return None, embed

        if command.get('help', False):
            return None, self.help_embed()

        elif command.get('command') == 'register':
            return None, await self.register(command)

        elif command.get('command') == 'unregister':
            return None, await self.unregister(command)

        elif command.get('command') == 'list':
            return None, await self.list(command)

        return None, None
