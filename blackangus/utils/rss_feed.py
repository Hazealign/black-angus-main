from time import mktime, struct_time
from typing import List, Optional

import feedparser
import httpx
import pendulum
from feedparser import FeedParserDict


class RSSFetchException(BaseException):
    pass


async def fetch_rss_feed(
    link: str, latest_date: Optional[pendulum.DateTime] = None
) -> List[FeedParserDict]:
    """
    특정 링크의 RSS Feed를 받고, 마지막 시간이 있으면 그 시간 이후의 피드만 가져옵니다.

    :param link: RSS 링크
    :param latest_date: 마지막으로 가져온 글의 작성 시간
    :return:
    """
    timezone_seoul = pendulum.timezone('Asia/Seoul')  # type: ignore

    async with httpx.AsyncClient() as client:
        response = await client.get(link)

        if 'xml' not in response.headers['content-type']:
            raise RSSFetchException('RSS Feed에서 XML을 읽어오는데 실패했습니다.')

        data = feedparser.parse(response.text)

        if latest_date is None:
            return data.entries

        ret_val: List[FeedParserDict] = list()

        for entry in data.entries:
            dt = struct_time_to_pendulum_datetime(entry.published_parsed)
            latest_date = latest_date.astimezone(timezone_seoul)  # type: ignore

            if latest_date < dt:  # type: ignore
                ret_val.append(entry)

        return ret_val


def struct_time_to_pendulum_datetime(time: struct_time) -> pendulum.DateTime:
    dttm = pendulum.from_timestamp(mktime(time))
    return dttm.astimezone(pendulum.timezone('Asia/Seoul'))  # type: ignore
