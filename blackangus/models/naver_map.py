import dataclasses
from typing import List, Optional

import pendulum


@dataclasses.dataclass
class NaverMapDirectionProcessModel:
    # 'WALKING', 'BUS', 'SUBWAY' 중 하나임
    type: str

    # 이동 방법에 대한 안내
    instruction: str

    # 거리 및 이동 시간
    distance: int
    duration: int

    # 예상 출발 및 도착 시간
    departure_time: pendulum.DateTime
    arrival_time: pendulum.DateTime

    # 탑승 / 대체 가능한 교통 수단 이름
    name: List[str]

    # 지하철 방향
    headsign: Optional[str] = None

    # 도착 위치
    arrive_at: Optional[str] = None


@dataclasses.dataclass
class NaverMapDirectionModel:
    # 'BUS', 'SUBWAY', 'BUS_AND_SUBWAY', 'INTERCITY' 중 하나임
    type: str

    # 비어있을 수 있음.
    labels: List[str]

    # 요금
    fare: int

    # 거리 (미터 단위인듯)
    distance: int

    # 시간 (분 단위)
    duration: int
    walking_duration: int

    # 환승 횟수
    transfers: int

    # 출발 시간과 도착 시간
    departure_time: pendulum.DateTime
    arrival_time: pendulum.DateTime

    # 이동 과정
    processes: List[NaverMapDirectionProcessModel]
