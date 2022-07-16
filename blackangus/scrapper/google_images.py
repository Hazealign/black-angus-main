import urllib.parse
from typing import Optional, List

from blackangus.models.search import GoogleImagesModel
from blackangus.scrapper.base import BaseScrapper, ScrapperException


class GoogleImagesScrapper(BaseScrapper[GoogleImagesModel]):
    async def scrape(
        self, keyword: Optional[str], size: int
    ) -> List[GoogleImagesModel]:
        if keyword is None:
            raise ScrapperException('검색어가 없을 수 없습니다.')

        if size > 30:
            raise ScrapperException('최대 50개까지만 조회가 가능합니다.')

        page = await self.create_page()

        encoded_keyword = urllib.parse.quote_plus(keyword)
        await page.goto(
            f'https://www.google.com/search?q={encoded_keyword}&source=lnms&tbm=isch&sa=X',
            wait_until='networkidle',
        )

        for i in range(size):
            await page.mouse.wheel(delta_x=3, delta_y=1000)
            await page.wait_for_timeout(500)

        # 하나씩 결과를 가져와본다.
        # Selector 기반의 스크래퍼라서 웹이 개편되면 다시 따야함.

        titles = await page.evaluate(
            """
                () => Array.from(
                    document.querySelectorAll('img.rg_i.Q4LuWd')
                ).map(item => item.attributes.alt?.value)
            """
        )

        destination_links = await page.evaluate(
            """
                () => Array.from(
                    document.querySelectorAll('a.VFACy.kGQAp.sMi44c.d0NI4c.lNHeqe.WGvvNb')
                ).map(item => item.attributes.href?.value)
            """
        )

        # 실제 이미지를 가져오려면 하나하나 클릭해서 원본 이미지를 따야한다.
        # 번거롭지만 이렇게 해야함...
        image_links: List[str] = []

        for i in range(size):
            thumbnail_link_elem = await page.query_selector(
                selector=f'a.wXeWr.islib.nfEiy >> nth={i}'
            )
            if thumbnail_link_elem is not None:
                await thumbnail_link_elem.click()

            # 잠깐 기다렸다가,
            await page.wait_for_timeout(750)

            link_elem = await page.query_selector('img.n3VNCb.KAlRDb')

            if link_elem is None:
                image_links.append('')
                continue

            link = await link_elem.get_attribute('src')
            image_links.append(link if link is not None else '')

        results: List[GoogleImagesModel] = []

        for i in range(size):
            results.append(
                GoogleImagesModel(
                    image_link=image_links[i],
                    title=titles[i],
                    destination_link=destination_links[i],
                )
            )

        await page.close()
        return results
