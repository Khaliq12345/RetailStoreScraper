from copy import deepcopy
import json

from func_retry import retry
from src.domain.scraper_strategy import FullScraperStrategy

from src.infrastructure.scraping.walmart import config
from typing import Any, Optional
import httpx
from concurrent.futures import ThreadPoolExecutor
from src.domain.entities import ProductModel


class WalmartFullScraper(FullScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str, folder: str
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)

    def parse_one_item(self, item_raw: Any) -> Optional[ProductModel]:
        pass

    def scrape_one_category(self, category: str):
        json_data = deepcopy(config.full_json_data)
        response = httpx.post(
            "https://www.walmart.ca/orchestra/snb/graphql/browse?spelling=true&itemCount=0&isGuidedNav=false&categoryId=10019_6000194327370&ps=20&pageNumber=1&additionalQueryParams=%7BisMoreOptionsTileEnabled=true,%20isDynamicFacetsEnabled=false,%20isGenAiEnabled=false,%20view_module=null,%20isWicCacheAvailable=null,%20wicTransactionId=null,%20selectedIntent=null,%20categoryNupsEnabled=false%7D&fitmentFieldParams=&enablePortableFacets=false",
            headers=config.full_headers,
            data=json_data,
        )

    def start_scraping(self) -> None:
        return super().start_scraping()

