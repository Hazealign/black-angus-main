import asyncio
from datetime import datetime
from typing import List, Union, Optional
from uuid import uuid4

import boto3
import httpx
from mypy_boto3_s3 import S3Client

from blackangus.config import EmoticonConfig
from blackangus.services.emoticon import EmoticonException, transfer_file
from blackangus.models.emoticon.main import EmoticonModel, EmoticonListView


class EmoticonService:
    s3: S3Client
    s3_bucket: str
    httpx_client: httpx.AsyncClient

    # 기본적으로 사용할 S3, httpx 클라이언트를 셋업합니다.
    def __init__(self, config: EmoticonConfig):
        self.s3 = boto3.client(
            's3',
            region_name=config.s3_region,
            aws_access_key_id=config.s3_access_key,
            aws_secret_access_key=config.s3_secret_key,
        )

        self.s3_bucket = config.s3_bucket
        self.httpx_client = httpx.AsyncClient()

    # 새로운 이모티콘 모델을 생성합니다.
    async def create(self, name: str, raw_url: str) -> EmoticonModel:
        prev = await EmoticonModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

        if prev is not None:
            raise EmoticonException(f'이미 존재하는 이모티콘입니다: {name}')

        prim_path = f'images/emoticons/{uuid4()}'
        path = await transfer_file(
            http=self.httpx_client,
            url=raw_url,
            s3=self.s3,
            bucket=self.s3_bucket,
            s3_path=prim_path,
        )

        return await EmoticonModel(
            name=name,
            original_url=raw_url,
            image_path=path,
            removed=False,
        ).create()

    # 이모티콘을 복제합니다.
    @staticmethod
    async def duplicate(name: str, target: str) -> EmoticonModel:
        previous = await EmoticonModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

        if previous is None:
            raise EmoticonException(f'존재하지 않는 이모티콘입니다: {name}')

        previous_target = await EmoticonModel.find(
            {
                'name': target,
                'removed': False,
            }
        ).first_or_none()

        if previous_target is not None:
            raise EmoticonException(f'이미 존재하는 이모티콘입니다: {target}')

        return await EmoticonModel(
            name=target,
            original_url=previous.original_url,
            image_path=previous.image_path,
            removed=False,
        ).create()

    # 이모티콘 URL을 바꿉니다.
    async def update(
        self,
        name: str,
        new_url: str,
        update_equivalents: bool = False,
    ) -> Union[EmoticonModel, List[EmoticonModel]]:
        previous_list = await EmoticonModel.find(
            {
                'name': name,
                'removed': False,
            },
            limit=1,
        ).to_list(1)

        if len(previous_list) == 0:
            raise EmoticonException(f'존재하지 않는 이모티콘입니다: {name}')

        if update_equivalents:
            previous_list = await EmoticonModel.find(
                {
                    'original_url': previous_list[0].original_url,
                    'removed': False,
                }
            ).to_list()

        prim_path = f'images/emoticons/{uuid4()}'
        path = await transfer_file(
            http=self.httpx_client,
            url=new_url,
            s3=self.s3,
            bucket=self.s3_bucket,
            s3_path=prim_path,
        )

        await asyncio.gather(
            *map(
                lambda x: x.set(
                    {
                        'path': path,
                        'original_url': new_url,
                        'updated_at': datetime.now(),
                    }
                ),
                previous_list,
            )
        )

        return previous_list[0] if len(previous_list) == 1 else previous_list

    @staticmethod
    async def rename(before: str, after: str) -> EmoticonModel:
        previous = await EmoticonModel.find(
            {
                'name': before,
                'removed': False,
            }
        ).first_or_none()

        if previous is None:
            raise EmoticonException(f'존재하지 않는 이모티콘입니다: {before}')

        return await previous.set(
            {
                'name': after,
            }
        )

    # 특정 이름을 포함한 이모티콘을 검색합니다.
    @staticmethod
    async def search(name: str) -> List[EmoticonModel]:
        return await EmoticonModel.find(
            {
                'name': {'$regex': name, '$options': 'i'},
                'removed': False,
            }
        ).to_list()

    # 이모티콘을 삭제합니다.
    @staticmethod
    async def remove(name: str, remove_equivalents: bool = False):
        prev = await EmoticonModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

        if prev is None:
            raise EmoticonException(f'존재하지 않는 이모티콘입니다: {name}')

        await prev.set({'updated_at': datetime.now(), 'removed': True})

        if remove_equivalents:
            await asyncio.gather(
                *map(
                    lambda x: x.set(
                        {
                            'updated_at': datetime.now(),
                            'removed': True,
                        }
                    ),
                    await EmoticonModel.find(
                        {
                            'original_url': prev.original_url,
                            'removed': False,
                        }
                    ).to_list(),
                )
            )

    @staticmethod
    async def find_by_name(name: str) -> Optional[EmoticonModel]:
        return await EmoticonModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

    @staticmethod
    async def list_emoticons() -> List[str]:
        emoticons = await EmoticonModel.find(
            {
                'removed': False,
            },
            projection_model=EmoticonListView,
            sort='name',
        ).to_list()
        return [emoticon.name for emoticon in emoticons]

    @staticmethod
    async def get_equivalents(name: str) -> List[EmoticonModel]:
        emoticon = await EmoticonModel.find({'name': name}).first_or_none()

        if emoticon is None:
            raise EmoticonException(f'존재하지 않는 이모티콘입니다: {name}')

        origin_url = emoticon.original_url
        equivalents = await EmoticonModel.find({'origin_url': origin_url}).to_list()
        return equivalents
