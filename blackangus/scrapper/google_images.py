from typing import Optional, List

from blackangus.models.search import GoogleImagesModel
from blackangus.scrapper.base import BaseScrapper


class GoogleImagesScrapper(BaseScrapper[GoogleImagesModel]):
    async def scrape(
        self, keyword: Optional[str], size: int
    ) -> List[GoogleImagesModel]:
        raise NotImplementedError()
