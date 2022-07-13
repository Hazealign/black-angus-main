import asyncio
from math import floor
from typing import Optional, Dict, Any, Tuple

import discord
from discord import Color, Client, Embed

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.utils.google_geocoding_client import (
    GoogleAPIException,
    geocode_from_google,
)
from blackangus.utils.weather_client import (
    WeatherAPIException,
    get_weather_from_openweather,
    WeatherModel,
    get_air_pollution_from_openweather,
    AirPollutionModel,
)


class WeatherApp(PresentedResponseApp):
    disabled = False
    commands = ['날씨', 'weather']

    def __init__(
        self,
        config: Config,
        client: Client,
    ):
        self.config = config
        self.client = client

    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        parsed = ' '.join(context.clean_content.split(' ')[1:])
        return {'address': parsed}

    @staticmethod
    def create_embed(model: WeatherModel, pollution: AirPollutionModel) -> Embed:
        aqi_index = {
            1: '매우 좋음 (1단계)',
            2: '좋음 (2단계)',
            3: '보통 (3단계)',
            4: '나쁨 (4단계)',
            5: '매우 나쁨 (5단계)',
        }

        embed = (
            Embed(
                title=f'[{model.location}]의 날씨 정보',
                description=f'현재 온도는 {floor(model.current_temp)}도, 습도는 {model.humidity}%입니다.',
                color=Color.green(),
            )
            .add_field(
                name='날씨 상태', value=f'{model.status}, {model.description}', inline=False
            )
            .add_field(name='AQI', value=aqi_index[pollution.aqi])
            .add_field(name='기압', value=f'{model.pressure}hPa')
            .add_field(
                name='바람', value=f'{model.wind_degree}도 방향으로 {model.wind_speed}m/s'
            )
            .add_field(name='구름 수준', value=f'{model.cloudiness}%')
        )

        if pollution.co is not None:
            embed = embed.add_field(
                name='대기 중 일산화탄소 농도', value=f'{pollution.co:.2f} μg/m3'
            )

        if pollution.no is not None:
            embed = embed.add_field(
                name='대기 중 일산화질소 농도', value=f'{pollution.no:.2f} μg/m3'
            )

        if pollution.no2 is not None:
            embed = embed.add_field(
                name='대기 중 이산화질소 농도', value=f'{pollution.no2:.2f} μg/m3'
            )

        if pollution.o3 is not None:
            embed = embed.add_field(
                name='대기 중 오존 농도', value=f'{pollution.o3:.2f} μg/m3'
            )

        if pollution.so2 is not None:
            embed = embed.add_field(
                name='대기 중 이산화황 농도', value=f'{pollution.so2:.2f} μg/m3'
            )

        if pollution.nh3 is not None:
            embed = embed.add_field(
                name='대기 중 암모니아 농도', value=f'{pollution.nh3:.2f} μg/m3'
            )

        if pollution.pm2_5 is not None:
            embed = embed.add_field(name='초미세먼지', value=f'{pollution.pm2_5} μg/m3')

        if pollution.pm10 is not None:
            embed = embed.add_field(name='미세먼지', value=f'{pollution.pm10} μg/m3')

        if model.rain:
            rain_3h = 0 if model.rain_3h is None else model.rain_3h
            embed = embed.add_field(
                name='강우량',
                value=f'최근 1시간: {model.rain_1h} mm / 최근 3시간: {rain_3h} mm',
                inline=False,
            )

        if model.snow:
            snow_3h = 0 if model.snow_3h is None else model.snow_3h
            embed = embed.add_field(
                name='강설량',
                value=f'최근 1시간: {model.snow_1h} mm / 최근 3시간: {snow_3h} mm',
                inline=False,
            )

        return embed.set_footer(text='데이터 제공: Google / OpenWeather')

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        try:
            location = await geocode_from_google(self.config.google, command['address'])
            weather, pollution = await asyncio.gather(
                get_weather_from_openweather(self.config.weather, location),
                get_air_pollution_from_openweather(self.config.weather, location),
            )

            return None, self.create_embed(weather, pollution)
        except GoogleAPIException as e:
            return None, Embed(
                title='Google Geocoding API 오류',
                description=str(e),
                color=Color.red(),
            )
        except WeatherAPIException as e:
            return None, Embed(
                title='OpenWeather API 오류',
                description=str(e),
                color=Color.red(),
            )
