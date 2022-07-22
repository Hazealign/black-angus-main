import logging

import click

from blackangus.core import BotCore
from blackangus.migration.v1_to_v2 import V1V2Migrator


@click.group()
def blackangus():
    """
    여러 서버에서 돌아갈 수 있는 디목적 디스코드 봇
    """
    pass


@blackangus.command('migrate-from-v1')
@click.argument('v1-mongodb-url')
@click.argument('v1-image-path')
@click.argument('v2-config', default='./config.toml')
@click.option('--log-level', default='INFO')
def migrate(v1_mongodb_url: str, v1_image_path: str, v2_config: str, log_level: str):
    """
    v1 데이터베이스를 v2 데이터베이스로 변환합니다.
    """
    # 기본 로그 레벨은
    logging.basicConfig(level=log_level)
    return V1V2Migrator(v2_config, v1_image_path, v1_mongodb_url).run()


@blackangus.command('run')
@click.argument('config', default='./config.toml')
@click.option('--log-level', default='INFO')
def run(config: str, log_level: str):
    """
    봇을 실행합니다.
    :param config: 설정 파일
    :param log_level: 로그 레벨
    """
    logging.basicConfig(level=log_level)
    return BotCore(config).run()


if __name__ == '__main__':
    blackangus()
