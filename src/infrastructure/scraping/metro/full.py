import json
from typing import Any
from func_retry import retry
from selectolax.parser import HTMLParser, Node
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import FullScraperStrategy
from src.infrastructure.scraping.metro import config
import httpx


class BaseFullScraper(FullScraperStrategy):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.api_link = None
        self.headers = None
        self.categories = [
            "fruits-vegetables",
            "dairy-eggs",
            "pantry",
            "cooked-meals",
            "value-pack",
            "beverages",
            "beer-wine",
            "meat-poultry",
            "vegan-vegetarian-food",
            "organic-groceries",
            "snacks",
            "frozen",
            "bread-bakery-products",
            "deli-prepared-meals",
            "fish-seafood",
            "world-cuisine",
            "household-cleaning",
            "baby",
            "health-beauty",
            "pet-care",
            "pharmacy",
            "nature-s-signature",
        ]

    def parse_category(self, product_attributes: dict):
        """Parse categories of an item"""
        hierarchy = product_attributes.get("data-parent-category-hierarchy")
        aisle = category = sub_category = None
        if hierarchy is None:
            return aisle, category, sub_category
        match hierarchy.split("|"):
            case [sub_category, category, aisle, _]:
                aisle = aisle
                category = category
                sub_category = sub_category
            case [category, aisle, _]:
                aisle = aisle
                category = category
            case [aisle, _]:
                aisle = aisle
        return aisle, category, sub_category

    def get_price_from_attribute(self, product: Node):
        """Price helper"""
        for x in product.css("div"):
            if "data-main-price" in x.attributes:
                return x.attributes["data-main-price"]

    def get_price_per_quantity(self, product_html: Node, selector_str: str):
        """Price helper to get PPQ"""
        selectors = product_html.css(selector_str)
        match len(selectors):
            case 0:
                return [""]
            case 1:
                return [selectors[0].text(strip=True)]
            case _:
                return [s.text(strip=True) for s in selectors]

    def parse_price(self, product_html: Node):
        """Get the price info of an item"""
        PRICE_PER_QUANTITY = ".pricing__secondary-price span"
        BEFORE_PRICE = ".pricing__before-price"
        PROMO_DURATION = 'div[class="pricing__until-date"]'
        sale_price_html = product_html.css_first(BEFORE_PRICE)
        match sale_price_html:
            case None:
                regular_price = self.get_price_from_attribute(product_html)
                sale_price = None
                promo_duration = None
            case _:
                regular_price_node = product_html.css_first(BEFORE_PRICE)
                regular_price = (
                    regular_price_node.text() if regular_price_node else None
                )
                sale_price = self.get_price_from_attribute(product_html)
                promo_duration_node = product_html.css_first(PROMO_DURATION)
                promo_duration = (
                    promo_duration_node.text(strip=True)
                    if promo_duration_node
                    else None
                )

        price_per_quantity = self.get_price_per_quantity(
            product_html, PRICE_PER_QUANTITY
        )
        return regular_price, sale_price, price_per_quantity, promo_duration

    def parse_one_item(self, item_raw: Any):
        product_attributes = item_raw.attributes
        name = product_attributes.get("data-product-name-en")
        sku = product_attributes.get("data-product-code")
        brand = product_attributes.get("data-product-brand")
        aisle, category, sub_category = self.parse_category(product_attributes)
        regular_price, sale_price, price_per_quantity, promo_duration = (
            self.parse_price(item_raw)
        )
        size_node = item_raw.css_first('span[class="head__unit-details"]')
        size = size_node.text() if size_node else None
        image_node = item_raw.css_first("picture img")
        image = image_node.attributes.get("src")
        url_node = item_raw.css_first('a[class="product-details-link"]')
        url_path = url_node.attributes.get("href") if url_node else None
        url = f"https://www.{self.store}.ca{url_path}"
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
            Sale_Duration=promo_duration,
            UPC=None,
            Image=image,
            Url=url,
            Store_id=self.store_id,
        ).model_dump_json()
        product_json = json.loads(product_model)
        self.outputs.append(product_json)

    @retry(times=5, delay=10)
    def scrape_one_page(self, category: str, page: int) -> int:
        """Scrape one page"""
        response = httpx.get(
            f"{self.api_link}/{category}-page-{page}",
            headers=self.headers,
        )
        response.raise_for_status()
        soup = HTMLParser(response.text)
        products = soup.css(
            ".searchOnlineResults .default-product-tile.tile-product.item-addToCart"
        )
        print(f"Total products - {len(products)}")
        for product in products:
            self.parse_one_item(product)
        return len(products)

    def scrape_one_category(self, category: str):
        """Scrape item of one category"""
        page = 1
        while True:
            print(f"Page - {page}")
            total_page = self.scrape_one_page(category, page)
            if total_page < 5:
                break
            elif self.environment == "beta":
                break
            page += 1

    def start_scraping(self):
        """Start interation through all the items"""
        for category in self.categories:
            self.scrape_one_category(category)


class MetroFullScraper(BaseFullScraper):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.api_link = "https://api2.metro.ca/en/online-grocery/aisles"
        self.headers = config.metro_headers


class SupercFullScraper(BaseFullScraper):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.api_link = "https://api2.superc.ca/en/aisles"
        self.headers = config.superc_headers
