from selectolax.parser import HTMLParser
from src.domain.scraper_strategy import FullScraperStrategy
from src.infrastructure.scraping.metro import config
import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class BaseFullScraper(FullScraperStrategy):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = None
        self.headers = None

    def parse_one_item(self, item_raw: Any) -> None:
        # self.outputs.append(product_model)
        return super().parse_one_item(item_raw)

    def start_scraping(self):
        """Start interation through all the items"""
        pass


class MetroFullScraper(BaseFullScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.metro.ca/en/online-grocery/aisles/pantry/p"
        self.headers = config.metro_headers


class SupercFullScraper(BaseFullScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.superc.ca/en/aisles/pantry/p"
        self.headers = config.superc_headers
