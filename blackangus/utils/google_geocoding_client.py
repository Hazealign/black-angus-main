import urllib.parse
from typing import Tuple

import httpx

from blackangus.config import GoogleConfig


class GoogleAPIException(BaseException):
    pass


async def geocode_from_google(
    config: GoogleConfig, location: str
) -> Tuple[float, float]:
    """
    지정한 위치의 위도, 경도를 반환합니다.
    첫번째가 latitude, 두번째가 longitude입니다.
    """
    encoded_location = urllib.parse.quote(location)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://maps.googleapis.com/maps/api/geocode/json'
            f'?address={encoded_location}&key={config.api_key}'
        )

        if not response.is_success:
            raise GoogleAPIException(f'{response.status_code}: API 요청에 실패했습니다.')

        response_data = response.json()

        if (
            response_data.get('status', None) != 'OK'
            or len(response_data.get('results', list())) == 0
        ):
            raise GoogleAPIException(f'{response_data["status"]}: API 요청에 실패했습니다.')

        latitude = response_data['results'][0]['geometry']['location']['lat']
        longitude = response_data['results'][0]['geometry']['location']['lng']

        return latitude, longitude
