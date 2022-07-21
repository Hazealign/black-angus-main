import asyncio
from datetime import datetime
from io import BytesIO
from tempfile import TemporaryDirectory
from typing import List, Tuple, Optional, Dict
from uuid import uuid4

from apnggif import apnggif
import boto3
import httpx
from PIL import Image, PngImagePlugin
from mypy_boto3_s3 import S3Client

from blackangus.config import EmoticonConfig
from blackangus.models.emoticon.base_response import ResponseResultModel
from blackangus.models.emoticon.linecon import LineconModel
from blackangus.models.emoticon.linecon_response import (
    LineconCategoryListModel,
    LineconCategoryModel,
    LineconItemModel,
    LineconCategoryDetailModel,
)
from blackangus.models.emoticon.main import EmoticonModel, EmoticonFrom
from blackangus.services.emoticon import (
    RegionEnum,
    EmoticonException,
    transfer_file,
    download_file,
    transfer_file_from_bytes,
)
from blackangus.services.emoticon.main import EmoticonService


class LineconService:
    config: EmoticonConfig

    s3: S3Client
    s3_bucket: str

    httpx_client: httpx.AsyncClient

    # 기본적으로 사용할 S3, httpx 클라이언트를 셋업합니다.
    def __init__(self, config: EmoticonConfig):
        self.config = config
        self.s3 = boto3.client(
            's3',
            region_name=config.s3_region,
            aws_access_key_id=config.s3_access_key,
            aws_secret_access_key=config.s3_secret_key,
        )

        self.s3_bucket = config.s3_bucket
        self.httpx_client = httpx.AsyncClient()
        self.emoticon_service = EmoticonService(config)

    async def search_list_from_server(
        self,
        region: RegionEnum,
        keyword: str,
        page: int = 1,
        limit: int = 10,
    ) -> LineconCategoryListModel:
        endpoint = self.config.api_endpoint.get(region.value, None)
        if endpoint is None:
            raise EmoticonException('설정에 해당 Region의 Endpoint가 없습니다.')

        path = f'{endpoint}/api/v1/line/list'
        response = await self.httpx_client.get(
            path,
            params={
                'keyword': keyword,
                'page': page,
                'limit': limit,
            },
        )

        if not response.is_success:
            raise EmoticonException(
                f'[{response.status_code}] API 호출에 실패했습니다: {response.text}'
            )

        value = response.json()
        success = value.get('result', dict()).get('success', False)

        if not success:
            message = value.get('result', dict()).get('message', 'Unknown Error')
            error = value.get('result', dict()).get('error', None)
            pretty_printed = str(
                ResponseResultModel(
                    success=success,
                    message=message,
                    error=error,
                )
            )

            raise EmoticonException(f'API 호출에 실패했습니다: {pretty_printed}')

        counts: int = value.get('data', dict()).get('counts', 0)
        items: List[LineconCategoryModel] = []
        for item in value.get('data', dict()).get('items', []):
            items.append(
                LineconCategoryModel(
                    title=item['title'],
                    id=item['id'],
                    link=item['link'],
                )
            )

        return LineconCategoryListModel(
            counts=counts,
            items=items,
        )

    async def fetch_item_from_server(
        self,
        region: RegionEnum,
        linecon_id: int,
    ) -> LineconCategoryDetailModel:
        endpoint = self.config.api_endpoint.get(region.value, None)
        if endpoint is None:
            raise EmoticonException('설정에 해당 Region의 Endpoint가 없습니다.')

        path = f'{endpoint}/api/v1/line/{linecon_id}'
        response = await self.httpx_client.get(path, timeout=None)

        if not response.is_success:
            raise EmoticonException(
                f'[{response.status_code}] API 호출에 실패했습니다: {response.text}'
            )

        value = response.json()
        success = value.get('result', dict()).get('success', False)

        if not success:
            message = value.get('result', dict()).get('message', 'Unknown Error')
            error = value.get('result', dict()).get('error', None)
            pretty_printed = str(
                ResponseResultModel(
                    success=success,
                    message=message,
                    error=error,
                )
            )

            raise EmoticonException(f'API 호출에 실패했습니다: {pretty_printed}')

        item_id: int = value.get('data', dict()).get('item_id', None)

        if item_id is None:
            raise EmoticonException(f'API 호출에 실패했습니다: {response.text}.')

        title: str = value['data']['title']
        description: str = value['data']['description']
        author: str = value['data']['author']

        items: List[LineconItemModel] = []
        for item in value['data']['items']:
            items.append(
                LineconItemModel(
                    type=item['type'],
                    item_id=item['item_id'],
                    url=item['url'],
                    sound_url=item['sound_url'],
                )
            )

        return LineconCategoryDetailModel(
            item_id=item_id,
            title=title,
            description=description,
            author=author,
            items=items,
        )

    async def create_from_item(
        self,
        prefix: str,
        detail: LineconCategoryDetailModel,
    ) -> Tuple[LineconModel, List[EmoticonModel]]:
        prev_counts = await LineconModel.find(
            {
                'name': {
                    '$regex': f'^{prefix}',
                    '$options': 'i',
                },
                'removed': False,
            }
        ).count()

        if prev_counts > 0:
            raise EmoticonException(f'이미 이모티콘 중 {prefix}로 시작하는 이름이 있습니다.')

        category = await LineconModel(
            line_id=detail.item_id,
            name=prefix,
            title=detail.title,
        ).create()

        emoticons: List[EmoticonModel] = []

        tmpdir = TemporaryDirectory()

        for i in range(len(detail.items)):
            item = detail.items[i]
            current_id = uuid4()

            content = await download_file(self.httpx_client, item.url)
            image = Image.open(BytesIO(content))

            if item.type == 'animation' and (
                type(image) is PngImagePlugin.PngImageFile and image.is_animated
            ):
                animated_png = True
                exported_origin_path = f'{tmpdir.name}/{current_id}.png'
                exported_converted_path = f'{tmpdir.name}/{current_id}.gif'

                with open(exported_origin_path, 'wb') as file:
                    file.write(content)

                apnggif(
                    png=exported_origin_path,
                    gif=exported_converted_path,
                )
            else:
                animated_png = False
                exported_converted_path = None

            image.close()

            prim_path = f'images/emoticons/{current_id}'
            file_path = await transfer_file(
                http=self.httpx_client,
                url=item.url,
                s3=self.s3,
                bucket=self.s3_bucket,
                s3_path=prim_path,
            )

            if animated_png and exported_converted_path is not None:
                with open(exported_converted_path, 'rb') as file:
                    gif_file = BytesIO(file.read()).read()

                    gif_path = transfer_file_from_bytes(
                        content=gif_file,
                        extension='gif',
                        s3=self.s3,
                        bucket=self.s3_bucket,
                        s3_path=prim_path,
                    )
            else:
                gif_path = None

            emoticons.append(
                await EmoticonModel(
                    name=f'{prefix}_{i + 1}',
                    original_url=item.url,
                    image_path=gif_path if animated_png else file_path,
                    sound_url=item.sound_url if item.sound_url is not None else None,
                    original_image_path=file_path,
                    removed=False,
                    image_from=EmoticonFrom.LINE,
                    relation_id=category.id,
                ).create()
            )

        tmpdir.cleanup()
        return category, emoticons

    @staticmethod
    async def find_one_by_name(
        name: str,
    ) -> Optional[LineconModel]:
        return await LineconModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

    @staticmethod
    async def remove_item(
        name: str,
    ):
        detail = await LineconModel.find(
            {
                'name': name,
                'removed': False,
            }
        ).first_or_none()

        if detail is None:
            raise EmoticonException(f'{name} 이름의 이모티콘이 없습니다.')

        await detail.set(
            {
                'removed': True,
                'updated_at': datetime.now(),
            }
        )

        results = await EmoticonModel.find(
            {
                'relation_id': detail.id,
                'removed': False,
            }
        ).to_list()

        await asyncio.gather(
            *map(
                lambda result: result.set(
                    {
                        'removed': True,
                        'updated_at': datetime.now(),
                    }
                ),
                results,
            )
        )

    @staticmethod
    async def get_lists() -> Tuple[List[LineconModel], Dict[str, List[EmoticonModel]]]:
        linecons: List[LineconModel] = await LineconModel.find(
            {
                'removed': False,
            }
        ).to_list()

        dictionary: Dict[str, List[EmoticonModel]] = {}

        for linecon in linecons:
            dictionary[str(linecon.id)] = await EmoticonModel.find(
                {
                    'relation_id': linecon.id,
                    'removed': False,
                }
            ).to_list()

        return linecons, dictionary
