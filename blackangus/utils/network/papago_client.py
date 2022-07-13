import httpx

from blackangus.config import PapagoConfig

PAPAGO_LANGUAGE_MAP = {
    '한국어': 'ko',
    '영어': 'en',
    '일본어': 'ja',
    '중국어_간체': 'zh-CN',
    '중국어_번체': 'zh-TW',
    '베트남어': 'vi',
    '인도네시아어': 'id',
    '태국어': 'th',
    '독일어': 'de',
    '러시아어': 'ru',
    '스페인어': 'es',
    '이탈리아어': 'it',
    '프랑스어': 'fr',
}


class PapagoException(BaseException):
    pass


async def translate_from_papago(
    config: PapagoConfig, language_from: str, language_to: str, text: str
) -> str:
    """
    파파고로 API를 번역합니다.

    :param config: 파파고에 대한 API 설정
    :param language_from: 원문 언어, 자연어로 입력해야합니다.
    :param language_to: 번역될 언어, 자연어로 입력해야합니다.
    :param text: 번역할 텍스트
    :return: 번역된 결과
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Naver-Client-Id': config.client_id,
        'X-Naver-Client-Secret': config.client_secret,
    }

    data = {
        'source': PAPAGO_LANGUAGE_MAP[language_from],
        'target': PAPAGO_LANGUAGE_MAP[language_to],
        'text': text,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://openapi.naver.com/v1/papago/n2mt', data=data, headers=headers
        )

        if not response.is_success:
            raise PapagoException(f'{response.status_code}: API 요청에 실패했습니다.')

        response_data = response.json()
        return response_data['message']['result']['translatedText']
