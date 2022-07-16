import asyncio
from typing import Optional, Dict, Any, Tuple
import shlex

import pendulum
from discord import Client, Message, Embed, Color

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.models.naver_map import NaverMapDirectionModel
from blackangus.utils.network.google_geocoding_client import geocode_from_google
from blackangus.utils.network.naver_map_pathfinder_client import (
    find_transit_path_from_locations,
)


class NaverTransitDirectionApp(PresentedResponseApp):
    disabled = False
    commands = ['경로', '교통', 'transit', 'direction']

    def __init__(
        self,
        config: Config,
        client: Client,
    ):
        self.config = config
        self.client = client

    @staticmethod
    def help_embed() -> Embed:
        return Embed(
            title='네이버 경로 탐색 기능',
            description='네이버 지도의 비공식 API를 사용하여 대중교통 경로를 가져옵니다.\n'
            '지오코딩은 구글의 공식 API를 사용하고 있습니다.\n'
            '`경로(교통, transit, direction) --from 출발지 --to 도착지 [--time 시간] [--count 갯수]`을 입력해주세요.',
            color=Color.green(),
        )

    @staticmethod
    def result_to_embed(model: NaverMapDirectionModel) -> Embed:
        label = '' if len(model.labels) == 0 else f'[{", ".join(model.labels)}] '
        type_status = (
            '버스로만 이동합니다.'
            if model.type == 'BUS'
            else ('지하철로만 이동합니다.' if model.type == 'SUBWAY' else '복합적으로 이용합니다.')
        )

        embed = Embed(
            title=f'{label}{model.duration}분 소요 / {model.arrival_time.format("HH:mm")} 도착 예정',
            description=f'총 거리는 {(model.distance / 1000):.2f}km이며, '
            f'환승은 {model.transfers}회, {model.fare}원 예상입니다.\n'
            f'{type_status} '
            f'{model.walking_duration}분 정도 걷습니다. '
            f'출발 시간은 {model.departure_time.format("HH:mm")} 기준입니다.\n',
            color=Color.green(),
        )

        for i in range(len(model.processes)):
            process = model.processes[i]
            process_type = (
                '[버스]'
                if process.type == 'BUS'
                else '[지하철]'
                if process.type == 'SUBWAY'
                else '[기차]'
                if process.type == 'TRAIN'
                else '[시외버스]'
                if process.type == 'INTERCITYBUS'
                else '[걷기]'
            )
            names = f'**{", ".join(process.name)}**' if len(process.name) != 0 else ''
            arrive_result = (
                ''
                if process.arrive_at is None
                else f'\n**{process.arrive_at}**에서 내려야합니다.'
            )

            description = (
                f'{process_type} {names} {process.instruction}\n'
                f'{process.departure_time.format("HH:mm")} 출발 후 '
                f'{process.arrival_time.format("HH:mm")} 도착 예정\n'
                f'{(process.distance / 1000):.2f}km 이동으로 {process.duration}분 소요 예정{arrive_result}'
            )

            embed = embed.add_field(
                name=f'{i + 1}번째 과정',
                value=description,
                inline=True,
            )

        return embed

    async def parse_command(self, context: Message) -> Optional[Dict[str, Any]]:
        # noinspection PyTypeChecker
        parsed = shlex.split(context.clean_content)[1:]

        if '-h' in parsed or '--help' in parsed:
            return {'help': True}

        if '--from' not in parsed or '--to' not in parsed:
            return {'help': False, 'error': True}

        time = (
            pendulum.now()
            if '--time' not in parsed
            else pendulum.parse(parsed[parsed.index('--time') + 1])
        )
        address_from = parsed[parsed.index('--from') + 1]
        address_to = parsed[parsed.index('--to') + 1]
        count = (
            3 if '--count' not in parsed else int(parsed[parsed.index('--count') + 1])
        )

        return {
            'help': False,
            'error': False,
            'time': time,
            'address_from': address_from,
            'address_to': address_to,
            'count': count,
            'channel': context.channel.id,
        }

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        if command['help']:
            return None, self.help_embed()

        if command['error']:
            return None, Embed(
                title='오류',
                description='출발지와 도착지를 입력해주세요.',
                color=Color.red(),
            )

        try:
            (location_from, location_to) = await asyncio.gather(
                geocode_from_google(self.config.google, command['address_from']),
                geocode_from_google(self.config.google, command['address_to']),
            )

            results = await find_transit_path_from_locations(
                departure_time=command['time'],
                location_from=location_from,
                location_to=location_to,
            )

            channel = self.client.get_channel(command['channel'])
            count = (
                command['count'] if len(results) > command['count'] else len(results)
            )

            await channel.send(
                content=f'경로 추적을 통해 {len(results)}개의 결과를 찾았습니다. {count}개의 결과만 표시합니다.'
            )
            for i in range(count):
                await channel.send(embed=self.result_to_embed(results[i]))

        except Exception as e:
            return None, Embed(
                title='경로 탐색 오류',
                description=f'{e}',
                color=Color.red(),
            )

        return None, None
