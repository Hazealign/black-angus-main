from typing import Any, Dict, Optional

from discord import Message


async def parse_search_command(context: Message) -> Optional[Dict[str, Any]]:
    parsed = context.clean_content.split(' ')[1:]

    if '--help' in parsed or '-h' in parsed:
        return {'help': True}

    if len(str.strip(' '.join(parsed))) == 0:
        return {'help': True}

    # 처음 혹은 마지막에 count 옵션을 넣었을 때의 처리
    for index in [0, len(parsed) - 1]:
        item = parsed[index]

        if item.startswith('--count='):
            return {
                'help': False,
                'keyword': ' '.join(parsed[1:] if index == 0 else parsed[:index]),
                'count': int(item.split('=')[1]),
                'channel': context.channel.id,
            }

    return {
        'help': False,
        'count': 1,
        'keyword': ' '.join(parsed),
        'channel': context.channel.id,
    }
