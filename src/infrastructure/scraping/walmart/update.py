from copy import deepcopy
from typing import Any
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.walmart import config
import httpx
from concurrent.futures import ThreadPoolExecutor
from test import avec_sale, sans_sale



class WalmartUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)

    def parse_one_item(self, item_raw: Any) -> None:
        regular_price = (item_raw["priceInfo"]["wasPrice"]["priceString"] if item_raw["priceInfo"]["wasPrice"] != "None" else None) or None
        sale_price = (item_raw["priceInfo"]["currentPrice"]["priceString"] if item_raw["priceInfo"]["currentPrice"] != "None" else None) or None
        ppq_item = (item_raw["priceInfo"]["unitPrice"]["priceString"] if item_raw["priceInfo"]["unitPrice"] != "None" else None) or None 
        ppq = [ppq_item] if ppq_item else []
        name = item_raw["name"] or ""
        sku = item_raw["product_id"] or ""
        upc = item_raw["upc"] or ""
        brand = item_raw["brand"] or None
        size = None
        size_Label = None
        images_list = item_raw["imageInfo"]["allImages"] or []
        image_link = images_list[0]["url"] if len(images_list) > 0 else None
        item_url = item_raw["item_url"] or None
        category_list = item_raw["category"]["path"] or []
        aisle = (
            category_list[1]["name"]
            if len(category_list) > 1
            else (category_list[0]["name"] if len(category_list) > 0 else "")
        )
        category = category_list[2]["name"] if len(category_list) > 2 else ""
        sub_category = category_list[3]["name"] if len(category_list) > 3 else ""
        parsed_item = ProductModel(
            Regular_Price=regular_price,
            Sale_Price=sale_price,
            Price_Per_Quantity=ppq,
            #
            Aisle=aisle,
            Category=category,
            Sub_Category=sub_category,
            #
            Name=name,
            Sku=sku,
            Brand=brand,
            Size=size,
            Size_Label=size_Label,
            Sale_Duration=None,
            Image=image_link,
            Url=item_url,
            Store_id=self.store_id,
            UPC=upc,
        )
        print(parsed_item)
        print("end")
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
        # response.raise_for_status()
        # json_data = response.json()
        # product = json_data["data"]["product"]
        # if not product:
        #     return None
        # name = product["name"]
        # zip_code = product["location"]["postalCode"]
        # print(name, zip_code)
        product = sans_sale
        product["product_id"] = product_id
        product["item_url"] = item_url
        try:
            self.parse_one_item(product)
        except Exception as e:
            print(f"Error : {e}")

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
