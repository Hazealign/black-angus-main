import logging
import urllib.parse
from typing import List, Optional

from blackangus.models.search import YoutubeModel
from blackangus.scrapper.base import BaseScrapper, ScrapperException


class YoutubeScrapper(BaseScrapper[YoutubeModel]):
    async def scrape(self, keyword: Optional[str], size: int) -> List[YoutubeModel]:
        if keyword is None:
            raise ScrapperException('검색어가 없을 수 없습니다.')

        if size > 10:
            raise ScrapperException('최대 10개까지만 조회 가능합니다.')

        page = await self.create_page()

        encoded_keyword = urllib.parse.quote_plus(keyword)
        await page.goto(
            f'https://www.youtube.com/results?search_query={encoded_keyword}',
            wait_until='networkidle',
        )

        for i in range(size):
            await page.mouse.wheel(delta_x=3, delta_y=1000)
            await page.wait_for_timeout(1000)

        # 하나씩 결과를 추출해본다.
        # Selector 기반 스크래퍼이기 때문에 웹이 개편되면 다시 따야함

        thumbnail_links = await page.evaluate(
            f"""
            () => Array.from(
                document.querySelectorAll(
                    'ytd-video-renderer > div > ytd-thumbnail > a > ' +
                    'yt-img-shadow.style-scope.ytd-thumbnail.no-transition > img.style-scope.yt-img-shadow'
                )
            ).map(item => item.attributes.src?.nodeValue)
        """
        )
        logging.info(thumbnail_links)

        # 그냥 innerText로 자바스크립트에서 가져오면 안되어서 이런 불편한 방법을 쓰기로 함.
        duration_elements = await page.query_selector_all(
            selector="""
            ytd-video-renderer > div > ytd-thumbnail > a > div#overlays >
            ytd-thumbnail-overlay-time-status-renderer > span#text
        """
        )

        durations: List[str] = []
        for element in duration_elements:
            durations.append((await element.inner_text()).strip())

        titles = await page.evaluate(
            f"""
            () => Array.from(
                document.querySelectorAll(
                    'ytd-video-renderer > div#dismissible > div > div#meta > div#title-wrapper > h3 > a'
                )
            ).map(item => item.attributes['title'].nodeValue)
        """
        )
        logging.info(titles)

        descriptions = await page.evaluate(
            f"""
            () => Array.from(
                document.querySelectorAll(
                    'ytd-video-renderer > div#dismissible > div > ' +
                    'div.style-scope.ytd-video-renderer > yt-formatted-string'
                )
            ).map(item => item.innerText)
        """
        )
        logging.info(descriptions)

        uploader_names = await page.evaluate(
            f"""
            () => Array.from(
                document.querySelectorAll(
                    'ytd-video-renderer > div#dismissible > div > div > ' +
                    'ytd-channel-name#channel-name > div#container > div#text-container > yt-formatted-string'
                )
            ).map(item => item.innerText)
        """
        )
        logging.info(uploader_names)

        links = await page.evaluate(
            f"""
            () => Array.from(
                document.querySelectorAll(
                    'ytd-video-renderer > div#dismissible > div > div#meta > div#title-wrapper > h3 > a'
                )
            ).map(item => 'https://youtube.com' + item.attributes['href'].value)
        """
        )
        logging.info(links)

        results: List[YoutubeModel] = []

        for i in range(size):
            results.append(
                YoutubeModel(
                    thumbnail_link=thumbnail_links[i],
                    title=titles[i],
                    description=descriptions[i],
                    uploader=uploader_names[i],
                    link=links[i],
                    duration=durations[i],
                )
            )

        await page.close()
        return results
