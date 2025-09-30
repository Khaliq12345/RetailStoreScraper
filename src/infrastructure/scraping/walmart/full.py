from copy import deepcopy
import json

from func_retry import retry
from src.domain.scraper_strategy import FullScraperStrategy
from src.infrastructure.scraping.walmart import config
from typing import Any, Optional
import httpx
from src.domain.entities import ProductModel


# review categories with more than 25 pages


class WalmartFullScraper(FullScraperStrategy):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.categories = [
            "10019_6000194327370",
            "10019_6000194327369",
            "10019_6000194327357",
            "10019_6000194326346",
            "10019_6000194326337",
            "10019_6000194327359",
            "10019_6000194328523",
            "10019_6000194328523",
            "10019_6000194327356",
            "10019_6000194327377",
            "10019_6000195495824",
        ]
        self.categories_num = None

    def parse_category(self, item_raw: Any):
        """Parse a category"""
        aisle = category = sub_category = None
        bread_crumb = item_raw.get("category")
        if not bread_crumb:
            return None, None, None
        match bread_crumb.get("path"):
            case [_, aisle]:
                aisle = aisle.get("name")
            case [_, aisle, category]:
                aisle = aisle.get("name")
                category = category.get("name")
            case [_, aisle, category, sub_category]:
                aisle = aisle.get("name")
                category = category.get("name")
                sub_category = sub_category.get("name")

        return aisle, category, sub_category

    def parse_price(self, item_raw: Any):
        """Parse item prices"""
        price_info = item_raw.get("priceInfo")
        regular_price = sale_price = None
        price_per_quantity = []
        if price_info:
            current_price = price_info.get("currentPrice")
            was_price = price_info.get("wasPrice")
            unit_price = price_info.get("unitPrice")
            if (current_price) and (was_price):
                regular_price = was_price.get("price")
                sale_price = current_price.get("price")
            elif current_price:
                regular_price = current_price.get("price")
            price_per_quantity = [unit_price.get("priceString")] if unit_price else []
        return regular_price, sale_price, price_per_quantity

    def parse_one_item(self, item_raw: Any) -> Optional[ProductModel]:
        product_type = item_raw.get("__typename")
        if product_type != "Product":
            return None
        name = item_raw.get("name")
        brand = item_raw.get("brand")
        sku = item_raw.get("id")
        image_info = item_raw.get("imageInfo")
        image = image_info.get("thumbnailUrl") if image_info else None
        aisle, category, sub_category = self.parse_category(item_raw)
        regular_price, sale_price, price_per_quantity = self.parse_price(item_raw)
        cannonical_url = item_raw.get("canonicalUrl")
        url = f"https://www.walmart.ca{cannonical_url}"
        product_model = ProductModel(
            Aisle=aisle,
            Category=category,
            Sub_Category=sub_category,
            Regular_Price=regular_price,
            Sale_Price=sale_price,
            Price_Per_Quantity=price_per_quantity,
            Name=name,
            Sku=sku,
            Brand=brand,
            Size=None,
            Size_Label=None,
            Sale_Duration=None,
            UPC=None,
            Image=image,
            Url=url,
            Store_id=self.store_id,
        ).model_dump_json()
        product_json = json.loads(product_model)
        self.outputs.append(product_json)

    @retry(exc=httpx.ReadTimeout, times=5, delay=10)
    def scrape_one_page(self, params: dict) -> int:
        """Scrape one item"""
        username = ""
        password = ""
        proxy = f"http://{username}:{password}@ca.decodo.com:20000"
        response = httpx.get(
            "https://www.walmart.ca/orchestra/snb/graphql/Browse/777af326d413e63e99b502d275c59ec5441d8af3cdc1b882e040ae50e2219d6f/browse",
            params=params,
            headers=config.full_headers,
            cookies=config.full_cookies,
            # proxy=proxy,
        )
        response.raise_for_status()
        json_data = response.json()
        products = json_data["data"]["search"]["searchResult"]["itemStacks"][0][
            "itemsV2"
        ]
        for product in products:
            self.parse_one_item(product)
        print(f"Total products - {len(products)}")
        return len(products)

    def scrape_one_category(self, category_id: str) -> None:
        """Scrape all items from a category"""
        print(f"Category - {category_id}")
        json_data = deepcopy(config.full_json_data)

        # Update params
        page = 1
        limit = 60
        while True:
            print(f"Page - {page}")
            json_data["page"] = page
            json_data["catId"] = category_id
            json_data["limit"] = limit
            json_data["ps"] = limit

            # Encode back to JSON
            params = {"variables": json.dumps(json_data)}
            total_products = self.scrape_one_page(params)
            if total_products == 0:
                break
            page += 1

    def start_scraping(self) -> None:
        """Start Iterating through all categories"""

        # If we are targeting a particular category
        if (self.categories_num is not None) and (self.categories):
            self.scrape_one_category(self.categories[self.categories_num])
        else:
            for category in self.categories:
                self.scrape_one_category(category)
