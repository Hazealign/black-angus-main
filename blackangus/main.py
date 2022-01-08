import click

from blackangus.core import BotCore


@click.group()
def blackangus():
    """
    여러 서버에서 돌아갈 수 있는 디목적 디스코드 봇
    """
    pass


@blackangus.command('run')
@click.argument('config', default='./config.toml')
def run(config: str):
    """
    봇을 실행합니다.
    :param config: 설정 파일
    """
    return BotCore(config).run()


if __name__ == '__main__':
    blackangus()
