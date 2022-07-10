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
    def create_embed(model: WeatherModel) -> Embed:
        embed = (
            Embed(
                title=f'[{model.location}]의 날씨 정보',
                description=f'현재 온도는 {floor(model.current_temp)}도, 습도는 {model.humidity}%입니다.',
                color=Color.green(),
            )
            .add_field(name='날씨 상태', value=f'{model.status}, {model.description}')
            .add_field(name='기압', value=f'{model.pressure}hPa')
            .add_field(
                name='바람', value=f'{model.wind_degree}도 방향으로 {model.wind_speed}m/s'
            )
            .add_field(name='구름 수준', value=f'{model.cloudiness}%')
        )

        if model.rain:
            embed = embed.add_field(
                '강우량', value=f'최근 1시간: {model.rain_1h}mm / 최근 3시간: {model.rain_3h}mm'
            )

        if model.snow:
            embed = embed.add_field(
                '강설량', value=f'최근 1시간: {model.rain_1h}mm / 최근 3시간: {model.rain_3h}mm'
            )

        return embed.set_footer(text='데이터 제공: Google / OpenWeather')

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        try:
            location = await geocode_from_google(self.config.google, command['address'])
            weather = await get_weather_from_openweather(self.config.weather, location)

            return None, self.create_embed(weather)
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
