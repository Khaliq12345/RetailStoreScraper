from copy import deepcopy
from typing import Any
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.walmart import config
import httpx
from concurrent.futures import ThreadPoolExecutor


class WalmartUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)

    def parse_one_item(self, item_raw: Any) -> None:
        print(item_raw)
        parsed_item = ProductModel(
            Regular_Price=next(
                (
                    x["price"]
                    for x in item_raw["prices"]
                    if x["priceListType"] == "Regular"
                ),
                None,
            ),
            Sale_Price=next(
                (
                    x["price"]
                    for x in item_raw["prices"]
                    if x["priceListType"] == "Discount"
                ),
                None,
            ),
            Price_Per_Quantity=[
                f"{next((x['price'] for x in item_raw['prices'] if x['priceListType'] == 'Informational'), '')} / {item_raw['propertyBag']['ComparisonMeasure']['value']['en-CA']}"
            ],
            #
            Aisle="",
            Category="",
            Sub_Category="",
            #
            Name=f"{item_raw['propertyBag']['AdditionalInformation']['value']['en-CA']} {item_raw['displayName']['en-CA']}",
            Sku=item_raw["sku"],
            Brand=item_raw["propertyBag"]["BrandName"]["value"]["en-CA"],
            Size=str(item_raw["propertyBag"]["Size"]["value"]["en-CA"]).split(" ")[0],
            Size_Label=str(item_raw["propertyBag"]["Size"]["value"]["en-CA"]).split(
                " "
            )[1],
            Sale_Duration=None,
            Image=f"https://sbs-prd-cdn-products.azureedge.net/media/image/product/en/medium/{item_raw['propertyBag']['ProductImageFile']}".lower(),
            Url=item_raw["item_url"],
            Store_id=self.store_id,
            UPC=None,
        )
        print(parsed_item)
        self.outputs.append(parsed_item)
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
        product["product_id"] = product_id
        product["item_url"] = item_url
        self.parse_one_item(product)

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
