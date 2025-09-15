from selectolax.parser import HTMLParser
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.metro import config
import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class BaseUpdateScraper(UpdateScraperStrategy):
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
        self.get_all_product_links()
        print(f"Total product links - {len(self.product_links)}")
        self.update_multiple_items()

    def update_one_item(self, item_url: str) -> None:
        """Scrape one item"""
        product_id = item_url.split("/")[-1]
        print(f"--Scraping Item - {item_url}")
        response = httpx.get(
            f"{self.api_link}/{product_id}",
            headers=self.headers,
        )

        response.raise_for_status()
        soup = HTMLParser(response.text)
        print(soup.css_first("title").text())

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )


class MetroUpdateScraper(BaseUpdateScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.metro.ca/en/online-grocery/aisles/pantry/p"
        self.headers = config.metro_headers


class SupercUpdateScraper(BaseUpdateScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.superc.ca/en/aisles/pantry/p"
        self.headers = config.superc_headers
