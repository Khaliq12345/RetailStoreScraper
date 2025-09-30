from copy import deepcopy
import json

from func_retry import retry
from src.domain.scraper_strategy import FullScraperStrategy

from src.infrastructure.scraping.iga import config
from typing import Any
import httpx
from src.domain.entities import ProductModel


class IgaFullScraper(FullScraperStrategy):
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
            "Beverages",
            "Deli and Cheese",
            "Instore Bakery",
            "Bulk Foods",
            "Commercial Bakery",
            "Frozen",
            "Produce",
            "Grocery",
            "Health & Beauty",
            "Meat",
            "Home Meal Replacement",
            "Refrigerated Grocery",
            "Seafood",
        ]

    def parse_category(self, property_bag: dict):
        """Extract category of an item"""
        aisle = category = sub_category = None
        category_levels = {
            "aisle": "CategoryLevel1DisplayName",
            "category": "CategoryLevel2DisplayName",
            "sub_category": "CategoryLevel3DisplayName",
        }
        for level in category_levels:
            category_level = property_bag.get(category_levels[level])
            level_value = (
                category_level.get("value")[0] if category_level else None
            )
            match level:
                case "aisle":
                    aisle = level_value
                case "category":
                    category = level_value
                case "sub_category":
                    sub_category = level_value
        return aisle, category, sub_category

    def parse_one_item(self, item_raw: Any) -> None:
        """Parse one item details"""
        sku = item_raw.get("sku")
        price_info = item_raw.get("allPrices", {})
        regular_price = sale_price = comparison_measure = None
        if price_info:
            regular_price = price_info.get("regular")
            sale_price = price_info.get("sales")
            comparison_measure = price_info.get("comparaisonMeasure")
        property_bag = item_raw.get("propertyBag", {})
        name = property_bag.get("DisplayName")
        image_file = property_bag.get("ProductImageFile")
        image = f"https://sbs-prd-cdn-products.azureedge.net/media/image/product/en/medium/{image_file}"
        brand = property_bag.get("BrandName")
        size = property_bag.get("Size")
        size_comparison_measure = property_bag.get("ComparisonMeasure")
        aisle, category, sub_category = self.parse_category(property_bag)
        url = f"https://www.iga.net/en/product/{sku}"
        price_per_quantity = [
            f"{comparison_measure} / {size_comparison_measure}"
        ]
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
            Size=size,
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
    def scrape_one_page(self, start_index: int, json_data: dict) -> int:
        """Scrape just one page"""
        print(f"Starting from - {start_index}")
        json_data["query"]["startingIndex"] = start_index
        response = httpx.post(
            "https://ocscd.prd.sbs.orckestra.cloud/api/custom/search/IGA/en-CA/products",
            params=config.full_params,
            headers=config.full_headers,
            json=json_data,
        )
        response.raise_for_status()
        response_json = response.json()
        total = response_json.get("totalCount")
        products = response_json.get("documents")
        for product in products:
            self.parse_one_item(product)
        print(f"Total Products - {len(products)}")
        return total

    def scrape_one_category(self, category: str) -> None:
        """Scrape one category"""
        print(f"Scraping category - {category}")
        total = 0
        start_index = 0
        json_data = deepcopy(config.full_json_data)
        json_data["query"]["filter"]["filters"][3]["value"] = category
        while True:
            total = self.scrape_one_page(start_index, json_data)
            if total < start_index:
                break
            start_index += 100

    def start_scraping(self):
        """Start interation through all the categories"""
        print("Starting full scraping")
        for category in self.categories:
            self.scrape_one_category(category)

        print(f"Total Products Scraped - {len(self.outputs)}")
