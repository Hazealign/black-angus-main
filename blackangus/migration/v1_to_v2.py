import asyncio
import logging
from pathlib import Path
from uuid import uuid4

import boto3
import motor.motor_asyncio
from beanie import init_beanie

from blackangus.config import Config, load
from blackangus.models.emoticon.linecon import LineconModel
from blackangus.models.emoticon.main import EmoticonModel, EmoticonFrom
from blackangus.services.emoticon import transfer_file_from_bytes


class V1V2Migrator:
    """
    기존 TypeScript + Node.js 흑우봇에서 V2 흑우봇으로 MongoDB / 이미지를 마이그레이션시키는 프로그램.
    """

    def __init__(self, config: str, image_path: str, prev_mongodb_path: str):
        self.logger = logging.getLogger('blackangus:v1_v2_migrator')
        self.config: Config = load(Path(config))
        self.image_path = image_path
        self.prev_mongodb_path = prev_mongodb_path

        self.s3_bucket = self.config.emoticon.s3_bucket
        self.s3 = boto3.client(
            's3',
            region_name=self.config.emoticon.s3_region,
            aws_access_key_id=self.config.emoticon.s3_access_key,
            aws_secret_access_key=self.config.emoticon.s3_secret_key,
        )

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.migrate())
        loop.close()

    async def migrate(self):
        v1_db_client = motor.motor_asyncio.AsyncIOMotorClient(self.prev_mongodb_path)
        v2_db_client = motor.motor_asyncio.AsyncIOMotorClient(self.config.mongodb.url)

        v1_db = v1_db_client.get_default_database()
        assert v1_db is not None

        v1_session = await v1_db_client.start_session()
        v1_linecon = v1_db.get_collection('linecons')
        v1_lineconcategory = v1_db.get_collection('lineconcategories')
        v1_emoticon = v1_db.get_collection('emoticons')

        await init_beanie(
            database=v2_db_client[self.config.mongodb.database_name],
            document_models=[
                # 여기에 관련된 MongoDB 모델들을 넣어주세요.
                EmoticonModel,
                LineconModel,
            ],
        )

        # 라인 이모티콘부터 하나씩 해보자.
        async for category in v1_lineconcategory.find({}, session=v1_session):
            self.logger.info(f'Migrating linecon category: {category["name"]}')

            new_item = await LineconModel(
                name=category['name'],
                line_id=category['originId'],
                title=category['title'],
            ).create()

            async for legacy_item in v1_linecon.find(
                {
                    'category': category['_id'],
                    'removed': False,
                },
                session=v1_session,
            ):
                self.logger.info(f'Migrating linecon item: {legacy_item["name"]}')
                path = f'images/emoticons/{uuid4()}'

                file = open(f'{self.image_path}{legacy_item["fullPath"]}', 'rb')
                file_path = transfer_file_from_bytes(
                    content=file.read(),
                    extension=Path(legacy_item['fullPath']).suffix,
                    bucket=self.s3_bucket,
                    s3=self.s3,
                    s3_path=path,
                )

                await EmoticonModel(
                    name=legacy_item['name'],
                    original_url='',
                    image_path=file_path,
                    removed=False,
                    image_from=EmoticonFrom.LINE,
                    relation_id=new_item.id,
                    migrated_from_v1=True,
                ).create()

                file.close()

        # 이모티콘도 하나씩 해보자. 이건 더 쉽다.
        async for legacy_item in v1_emoticon.find(
            {
                'removed': False,
                'category': {
                    '$exists': False,
                },
            },
            session=v1_session,
        ):
            try:
                self.logger.info(f'Migrating emoticon item: {legacy_item["name"]}')
                path = f'images/emoticons/{uuid4()}'

                self.logger.debug(legacy_item)
                self.logger.debug(f'{self.image_path}{legacy_item["path"]}')

                file = open(f'{self.image_path}{legacy_item["path"]}', 'rb')
                file_path = transfer_file_from_bytes(
                    content=file.read(),
                    extension=Path(legacy_item['path']).suffix.replace('.', ''),
                    bucket=self.s3_bucket,
                    s3=self.s3,
                    s3_path=path,
                )

                if len(legacy_item.get('equivalents', list())) > 0:
                    names = [legacy_item['name'], *legacy_item['equivalents']]
                else:
                    names = [legacy_item['name']]

                await asyncio.gather(
                    *map(
                        lambda x: EmoticonModel(
                            name=x,
                            original_url='',
                            image_path=file_path,
                            removed=False,
                            image_from=EmoticonFrom.WEB,
                            migrated_from_v1=True,
                        ).create(),
                        names,
                    )
                )

                file.close()
            except Exception as e:
                self.logger.error(
                    f'Failed to migrate emoticon item: {legacy_item["name"]}'
                )
                self.logger.error(str(e))

        await v1_session.end_session()
        self.logger.info('Migration completed.')
