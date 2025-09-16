from copy import deepcopy
from typing import Any
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.walmart import config
import httpx
from concurrent.futures import ThreadPoolExecutor
from test import avec_sale, sans_sale
from typing import Any


class WalmartUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str, folder: str
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)

    def parse_one_item(self, item_raw: Any):
        return super().parse_one_item(item_raw)

    def parse_one_item(self, item_raw: Any) -> None:
        price_info = item_raw.get("priceInfo")
        wasPrice = price_info.get("wasPrice") if price_info else None
        currentPrice = price_info.get("currentPrice") if price_info else None
        unitPrice = price_info.get("unitPrice") if price_info else None
        regular_price = (
            wasPrice.get("priceString") if (wasPrice and wasPrice != "None") else None
        )
        sale_price = (
            currentPrice.get("priceString")
            if (currentPrice and currentPrice != "None")
            else None
        )
        ppq_item = (
            unitPrice.get("priceString")
            if (unitPrice and unitPrice != "None")
            else None
        )
        ppq = [ppq_item] if ppq_item else []
        name = item_raw.get("name", "")
        sku = item_raw.get("product_id", "")
        upc = item_raw.get("upc")
        brand = item_raw.get("brand")
        size = None
        size_Label = None
        imageInfo = item_raw.get("imageInfo")
        images_list = imageInfo.get("allImages", [])
        image_first = images_list[0] if len(images_list) > 0 else None
        image_link = image_first.get("url") if image_first else None
        item_url = item_raw.get("item_url")
        category = item_raw.get("category")
        category_list = category.get("path", [])
        aisle = category_name = sub_category = None
        match category_list:
            case [a, b]:
                aisle = b.get("name")
            case [a, b, c]:
                aisle = b.get("name")
                category_name = c.get("name")
            case [a, b, c, d, *rest]:
                aisle = b.get("name")
                category_name = c.get("name")
                sub_category = d.get("name")
        parsed_item = ProductModel(
            Regular_Price=regular_price,
            Sale_Price=sale_price,
            Price_Per_Quantity=ppq,
            #
            Aisle=aisle,
            Category=category_name,
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
        self.parse_one_item(product)

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
