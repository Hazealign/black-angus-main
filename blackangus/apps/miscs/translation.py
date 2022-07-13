from typing import Any, Dict, Optional, Tuple

import discord
from discord import Client, Color, Embed

from blackangus.apps.base import PresentedResponseApp
from blackangus.config import Config
from blackangus.utils.network.papago_client import (
    PapagoException,
    translate_from_papago,
)


class TranslationApp(PresentedResponseApp):
    disabled = False
    commands = ['번역', 'translate', 'translation']

    def __init__(
        self,
        config: Config,
        client: Client,
    ):
        self.config = config
        self.client = client

    async def parse_command(self, context: discord.Message) -> Optional[Dict[str, Any]]:
        parsed = context.clean_content.split(' ')

        if '--help' in parsed or '-h' in parsed:
            return {'help': True}

        return {
            'help': False,
            'language_from': parsed[1],
            'language_to': parsed[2],
            'text': ' '.join(parsed[3:]),
        }

    @staticmethod
    def help_embed() -> Embed:
        return Embed(
            title='파파고 번역',
            description='`한국어`, `영어`, `일본어`, `중국어_간체`, `중국어_번체`, `베트남어`, '
            '`인도네시아어`, `태국어`, `독일어`, `러시아어`, `스페인어`, `이탈리아어`, '
            '`프랑스어`에 대한 번역을 지원합니다. `!번역 원문언어 번역언어 텍스트`로'
            '입력해주세요.',
            color=Color.green(),
        )

    async def present(
        self, command: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Embed]]:
        if command.get('help', False):
            return None, self.help_embed()

        try:
            result = await translate_from_papago(
                self.config.papago,
                command['language_from'],
                command['language_to'],
                command['text'],
            )

            return None, Embed(
                title='파파고 번역 결과',
                description=result,
                color=Color.green(),
            )
        except PapagoException as e:
            return None, Embed(
                title='파파고 번역 실패',
                description=e.args[0],
                color=Color.red(),
            )
