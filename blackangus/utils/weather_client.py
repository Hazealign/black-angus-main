import dataclasses
from typing import Tuple, Optional
import urllib.parse

import httpx

from blackangus.config import WeatherConfig


class WeatherAPIException(BaseException):
    pass


@dataclasses.dataclass
class WeatherModel:
    location: str

    # 현재, 최고/최소 온도, 습도 및 기압, 가시거리
    current_temp: float
    min_temp: float
    max_temp: float
    feel_temp: float
    humidity: int
    pressure: float
    visibility: int

    # 바람의 세기와 각도
    wind_speed: float
    wind_degree: int

    # 구름 정도
    cloudiness: int

    # 강우 유무
    rain: bool
    rain_1h: Optional[float]
    rain_3h: Optional[float]

    # 강설 유무
    snow: bool
    snow_1h: Optional[float]
    snow_3h: Optional[float]

    # 날씨 설명
    status: str
    description: str


async def get_weather_from_openweather(
    config: WeatherConfig, location: Tuple[float, float]
) -> WeatherModel:
    """
    OpenWeather에서 위도와 경도를 바탕으로 날씨를 가져옵니다.
    데이터는 정규화해서 모델 객체로 반환합니다.

    :param config: API Key가 담긴 설정값
    :param location: 위경도 튜플(첫번쨰가 latitude, 두번째가 longitude)
    :return: 정규화된 모델 객체
    """
    data = urllib.parse.urlencode(
        {
            'lat': location[0],
            'lon': location[1],
            'appid': config.api_key,
            'units': 'metric',
        },
        doseq=True,
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.openweathermap.org/data/2.5/weather?' + data
        )

        if not response.is_success:
            raise WeatherAPIException(f'{response.status_code}: API 요청에 실패했습니다.')

        response_data = response.json()

        rain = response_data.get('rain', None) is not None
        snow = response_data.get('snow', None) is not None

        return WeatherModel(
            location=response_data['name'],
            current_temp=response_data['main']['temp'],
            min_temp=response_data['main']['temp_min'],
            max_temp=response_data['main']['temp_max'],
            feel_temp=response_data['main']['feels_like'],
            humidity=response_data['main']['humidity'],
            pressure=response_data['main']['pressure'],
            visibility=response_data['visibility'],
            wind_speed=response_data['wind']['speed'],
            wind_degree=response_data['wind']['deg'],
            cloudiness=response_data['clouds']['all'],
            rain=rain,
            rain_1h=response_data['rain']['1h'] if rain else None,
            rain_3h=response_data['rain']['3h'] if rain else None,
            snow=snow,
            snow_1h=response_data['snow']['1h'] if snow else None,
            snow_3h=response_data['snow']['3h'] if snow else None,
            status=response_data['weather'][0]['main'],
            description=response_data['weather'][0]['description'],
        )
