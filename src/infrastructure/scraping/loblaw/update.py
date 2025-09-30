import json
from urllib.parse import urljoin
from func_retry import retry
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.loblaw import config
from typing import Any, Optional
import httpx
from src.domain.entities import ProductModel
from dateparser import parse

STORES = {
    "provigo": {"id": "7297", "url": "https://www.provigo.ca/"},
    "maxi": {"id": "7234", "url": "https://www.maxi.ca/"},
}


class LoblawUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)

    def get_breadcrumb(self, breadcrumbs) -> tuple:
        """Get the breadcrumbs of a product/item"""
        match breadcrumbs[-3:]:
            case [aisle, category, subcategory]:
                return aisle["name"], category["name"], subcategory["name"]
            case [aisle, category]:
                return aisle["name"], category["name"], None
            case [aisle]:
                return aisle["name"], None, None
            case _:
                return None, None, None

    def parse_price(self, price_info: dict) -> tuple:
        """parse the price for one item"""
        wasPrice = price_info["wasPrice"]
        price = price_info["price"]
        comparisons = price_info["comparisonPrices"]
        match wasPrice:
            case None:
                regular_price = price["value"]
                sale_price = None
            case _:
                regular_price = wasPrice["value"]
                sale_price = price["value"]
        price_per_quantity = [
            f"${comp['value']}/{comp['quantity']}{comp['unit']}"
            for comp in comparisons
        ]
        return regular_price, sale_price, price_per_quantity

    def parse_one_item(self, item_raw: Any) -> Optional[ProductModel]:
        """Parse and Validate one item"""
        name = item_raw["name"]
        sku = item_raw["code"]
        brand = item_raw["brand"]
        price_info = item_raw["offers"]
        regular_price, sale_price, ppq = self.parse_price(price_info[0])
        sale_duration = None
        size = item_raw["packageSize"]
        try:
            image = item_raw["imageAssets"][0]["largeUrl"]
        except Exception as e:
            print(f"Image Error: {e}")
            image = None
        url = item_raw["link"]
        url = urljoin(STORES[f"{self.store}"]["url"], url)
        size_label = None
        breadcrumbs = item_raw["breadcrumbs"]
        aisle, category, subcategory = self.get_breadcrumb(breadcrumbs)
        product_model = ProductModel(
            Name=name,
            Aisle=aisle,
            Category=category,
            Sub_Category=subcategory,
            Sku=sku,
            Brand=brand,
            Regular_Price=regular_price,
            Sale_Price=sale_price,
            Price_Per_Quantity=ppq,
            Sale_Duration=sale_duration,
            Size=size,
            Image=image,
            Url=url,
            Size_Label=size_label,
            Store_id=self.store_id,
            UPC=None,
        ).model_dump_json()
        product_json = json.loads(product_model)
        print(product_json)
        self.outputs.append(product_json)

    @retry(times=5, delay=5)
    def update_one_item(self, item_url: str) -> None:
        """Updating one item and validate it"""
        sku = item_url.split("/")[-1]
        if not sku:
            return None
        date_parsed = parse("today")
        date_str = None
        if date_parsed:
            date_str = date_parsed.strftime("%d%m%Y")
        print(f"Scraping Item: {item_url} - Lang: {self.lang} ")
        params = {
            "lang": self.lang,
            "date": date_str,
            "pickupType": "STORE",
            "storeId": f"{STORES[f'{self.store}']['id']}",
            "banner": self.store,
        }
        try:
            response = httpx.get(
                f"https://api.pcexpress.ca/pcx-bff/api/v1/products/{sku}",
                params=params,
                headers=config.HEADERS,
                # proxy=self.proxy_string("ca"),
            )
            print(f"Response: {response.status_code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            json_data = response.json()
            self.parse_one_item(json_data)
        except Exception as e:
            print(f"Error: {e}")
