from enum import Enum


# Base Exception
from io import BytesIO
from typing import Tuple
from urllib.parse import urlparse

import httpx
from mypy_boto3_s3 import S3Client

from blackangus.models.emoticon.main import EmoticonModel


class EmoticonException(BaseException):
    pass


# 서버 위치에 대한 Region Enum
class RegionEnum(Enum):
    KR = 'kr'
    JP = 'jp'


# 이 이미지의 확장자를 URL에서 파악합니다. 복잡한 이미지 컨텐츠 분석은 하지 않습니다.
def get_extension_of_file(url: str) -> str:
    parsed = urlparse(url).path.split('.')[-1]
    return parsed if parsed in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else 'jpg'


# 이미지 다운로드, 최대 3회 재시도함
async def download_file(
    http: httpx.AsyncClient,
    url: str,
):
    response = await http.get(url)

    for i in range(3):
        if not response.is_success:
            response = await http.get(url)
        else:
            break

    if not response.is_success:
        raise EmoticonException(f'이미지 다운로드에 실패했습니다: {response.status_code}')

    return response.content


def transfer_file_from_bytes(
    content: bytes,
    extension: str,
    s3: S3Client,
    bucket: str,
    s3_path: str,
) -> str:
    key = f'{s3_path}.{extension}'

    try:
        s3.put_object(
            Bucket=bucket,
            Body=content,
            Key=key,
        )

        return key
    except Exception as e:
        raise EmoticonException(f'S3 저장에 실패했습니다: {e}')


# 특정 URL의 파일을 다운로드하고, S3에 올립니다.
async def transfer_file(
    http: httpx.AsyncClient,
    url: str,
    s3: S3Client,
    bucket: str,
    s3_path: str,
) -> str:
    data = await download_file(http, url)
    return transfer_file_from_bytes(
        data,
        get_extension_of_file(url),
        s3,
        bucket,
        s3_path,
    )


# 디스코드에서 쓰기 위해 파일을 다운로드 받습니다.
def download_emoticon(
    s3: S3Client, bucket: str, model: EmoticonModel
) -> Tuple[str, BytesIO]:
    exists_result = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=model.image_path,
    )

    if 'Contents' not in exists_result:
        raise EmoticonException(f'{model.name}에 대한 이미지를 찾을 수 없습니다.')

    file_name = model.image_path.split('/')[-1]
    file = BytesIO(
        s3.get_object(
            Bucket=bucket,
            Key=model.image_path,
        )['Body'].read()
    )

    return file_name, file
