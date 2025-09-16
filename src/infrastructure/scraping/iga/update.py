from copy import deepcopy
from src.domain.scraper_strategy import UpdateScraperStrategy

from src.infrastructure.scraping.iga import config
from typing import Any
import httpx
from concurrent.futures import ThreadPoolExecutor


class IgaUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str, folder: str
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)

    def parse_one_item(self, item_raw: Any) -> None:
        return

    def start_scraping(self):
        """Start interation through all the items"""
        self.get_all_product_links()
        print(f"Total product links - {len(self.product_links)}")
        self.update_multiple_items()

    def update_one_item(self, item_url: str) -> None:
        """Scrape one item"""
        product_id = item_url.split("/")[-1]
        print(f"--Scraping Item - {item_url}")
        json_data = deepcopy(config.json_data)
        json_data["productIds"] = [product_id]
        response = httpx.post(
            "https://ocscd.prd.sbs.orckestra.cloud/api/products/v2/10593D1/byIds",
            headers=config.headers,
            json=json_data,
            # proxy=self.proxy_string("ca"),
            # timeout=60,
        )
        print(f"--Response status for item - {item_url} - {response.status_code} ")
        response.raise_for_status()
        json_data = response.json()
        products = json_data.get("products")
        if not products:
            return None
        product = products[0]
        print(product["displayName"]["en-CA"])

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
