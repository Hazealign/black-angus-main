import datetime
from typing import Tuple, List
from urllib.parse import urlencode

import httpx
import pendulum

from blackangus.models.naver_map import (
    NaverMapDirectionModel,
    NaverMapDirectionProcessModel,
)


class NaverMapClientException(BaseException):
    pass


async def find_transit_path_from_locations(
    departure_time: pendulum.DateTime,
    location_from: Tuple[float, float],
    location_to: Tuple[float, float],
) -> List[NaverMapDirectionModel]:
    """
    네이버 지도 API를 통해 최적의 교통편을 찾아줍니다.
    주의: 이것은 API를 후킹해서 쓰고 있는 것이기 때문에 막히거나 변경될 가능성이 있습니다.

    :param departure_time: 출발 시간
    :param location_from: 출발 위치 (latitude, longitude 순서)
    :param location_to: 도착 위치 (latitude, longitude 순서)
    :return:
    """
    ua = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        ' AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1'
        ' Safari/605.1.15'
    )

    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'map.naver.com',
        'User-Agent': ua,
        'Referer': 'https://map.naver.com',
        'Connection': 'keep-alive',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    query_params = {
        'start': f'{location_from[1]},{location_from[0]}',
        'goal': f'{location_to[1]},{location_to[0]}',
        'crs': 'EPSG:4326',
        # API 쏘는걸 보니까 ISO 8601 타입에서 시간대는 빼고 보내는 것 같음.
        'departure_time': departure_time.to_iso8601_string().replace('+09:00', ''),
        'mode': 'TIME',
        'lang': 'ko',
        'includeDetailOperation': True,
    }

    tz = pendulum.timezone('Asia/Seoul')  # type: ignore

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://map.naver.com/v5/api/transit/directions/point-to-point?{urlencode(query_params)}',
            headers=headers,
        )

        if not response.is_success:
            raise NaverMapClientException(f'{response.status_code}: API 요청에 실패했습니다.')

        response_data = response.json()

        if len(response_data.get('paths', list())) == 0:
            raise NaverMapClientException(f'갈 수 경로가 없습니다.')

        results: List[NaverMapDirectionModel] = []

        try:
            for path in response_data['paths']:
                direction_type = path['type']
                labels = list(map(lambda x: x.get('labelText', ''), path['pathLabels']))
                fare = path['fare']
                distance = path['distance']
                duration = path['duration']
                walking_duration = path['walkingDuration']
                transfers = path['transferCount']

                if type(path['departureTime']) is datetime.datetime:
                    departure_time = pendulum.instance(path['departureTime'], tz=tz)
                else:
                    departure_time = pendulum.parse(path['departureTime'], tz=tz)  # type: ignore

                if type(path['arrivalTime']) is datetime.datetime:
                    arrival_time = pendulum.instance(path['arrivalTime'], tz=tz)
                else:
                    arrival_time = pendulum.parse(path['arrivalTime'], tz=tz)  # type: ignore

                processes: List[NaverMapDirectionProcessModel] = []

                for process in path['legs'][0]['steps']:
                    process_type = process['type']
                    process_instruction = process['instruction']
                    process_distance = process['distance']
                    process_duration = process['duration']
                    process_headsign = process['headsign']
                    process_name = list(
                        map(lambda x: x.get('longName', '없음'), process['routes'])
                    )

                    process_stations = process.get('stations', list())
                    if len(process_stations) == 0:
                        process_arrive_at = None
                    else:
                        process_arrive_at = process_stations[-1].get(
                            'displayName', None
                        )

                    if type(process['departureTime']) is datetime.datetime:
                        process_departure_time = pendulum.instance(
                            process['departureTime'], tz=tz
                        )
                    else:
                        process_departure_time = pendulum.parse(
                            process['departureTime'], tz=tz
                        )  # type: ignore

                    if type(process['arrivalTime']) is datetime.datetime:
                        process_arrival_time = pendulum.instance(
                            path['arrivalTime'], tz=tz
                        )
                    else:
                        process_arrival_time = pendulum.parse(
                            path['arrivalTime'], tz=tz
                        )  # type: ignore

                    processes.append(
                        NaverMapDirectionProcessModel(
                            type=process_type,
                            instruction=process_instruction,
                            distance=process_distance,
                            duration=process_duration,
                            headsign=process_headsign,
                            name=process_name,
                            departure_time=process_departure_time,
                            arrival_time=process_arrival_time,
                            arrive_at=process_arrive_at,
                        )
                    )

                results.append(
                    NaverMapDirectionModel(
                        type=direction_type,
                        labels=labels,
                        fare=fare,
                        distance=distance,
                        duration=duration,
                        walking_duration=walking_duration,
                        transfers=transfers,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        processes=processes,
                    )
                )
        except Exception as e:
            raise NaverMapClientException(f'결과 처리 과정 중 실패했습니다: {e}')

        return results
