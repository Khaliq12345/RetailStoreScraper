from copy import deepcopy
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.walmart import config
import httpx
from concurrent.futures import ThreadPoolExecutor


class WalmartUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)

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
        json_data["variables"]["itId"] = f"{product_id}"
        response = httpx.post(
            "https://www.walmart.ca/orchestra/pdp/graphql",
            headers=config.headers,
            json=json_data,
        )
        print(f"--Response status for item - {item_url} - {response.status_code} ")
        response.raise_for_status()
        json_data = response.json()
        product = json_data["data"]["product"]
        if not product:
            return None
        name = product["name"]
        zip_code = product["location"]["postalCode"]
        print(name, zip_code)

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
