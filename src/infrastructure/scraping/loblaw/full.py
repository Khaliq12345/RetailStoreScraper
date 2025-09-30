from copy import deepcopy
import json
from urllib.parse import urljoin
from func_retry import retry
from src.domain.scraper_strategy import FullScraperStrategy
from src.infrastructure.scraping.loblaw import config
from typing import Any, List, Optional
import httpx
from src.domain.entities import ProductModel
from dateparser import parse
import json_flatten


PRODUCT_GRID = "layout.sections.productListingSection.components.[0].data.productGrid"
PRODUCTS = f"{PRODUCT_GRID}.productTiles"
BREADCRUMBS = "layout.sections.productListingSection.components.[0].data.breadcrumbs"
NAVIGATION = "layout.sections.categoryNavigationSection.components.[0].data.navigation.childNodes"
TITLE = "title"
BRAND = "brand"
PRODUCT_ID = "productId"
IMAGE = "productImage.[0].imageUrl"
LINK = "link"
PACKAGE_SIZING = "packageSizing"
CURRENT_PAGE_SIZE = f"{PRODUCT_GRID}.pagination.pageSize$int"
HAS_MORE = f"{PRODUCT_GRID}.pagination.hasMore$bool"


class LoblawFullScraper(FullScraperStrategy):
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
            "28000",
            "28003",
            "27998",
            "28006",
            "58044",
            "57025",
            "28005",
            "28189",
            "28002",
            "27996",
            "28004",
            "28001",
            "27999",
        ]

    def parse_price(self, idx: int, flattened_json: dict):
        "extract prices from json"
        was_price = str(flattened_json.get(f"{PRODUCTS}.[{idx}].pricing.wasPrice"))
        if was_price != "None":
            reg_price = flattened_json.get(f"{PRODUCTS}.[{idx}].pricing.wasPrice")
            sale_price = flattened_json.get(f"{PRODUCTS}.[{idx}].pricing.price")
            return (reg_price, sale_price)
        else:
            reg_price = flattened_json.get(f"{PRODUCTS}.[{idx}].pricing.price")
            sale_price = None
            return (reg_price, sale_price)

    def get_breadcrumbs(self, flattened_json: dict):
        "extract the breadcrumbs of the product"
        aisle = flattened_json.get(f"{BREADCRUMBS}.[1].text")
        category = flattened_json.get(f"{BREADCRUMBS}.[2].text")
        sub_category = flattened_json.get(f"{BREADCRUMBS}.[3].text")
        return aisle, category, sub_category

    def get_value(self, idx: int, flattened_json: dict, value: str) -> str | None:
        return flattened_json.get(f"{PRODUCTS}.[{idx}].{value}")

    def parse_one_item(self, item_raw: Any) -> Optional[ProductModel]:
        page_size = int(item_raw.get(CURRENT_PAGE_SIZE))
        print(f"Page size: {page_size}")
        for i in range(0, page_size):
            try:
                product_json = item_raw[f"{PRODUCTS}.[{i}].title"]
            except KeyError:
                print("NO MORE DATA")
                break
            name = self.get_value(i, item_raw, TITLE)
            if not name:
                break
            brand = self.get_value(i, item_raw, BRAND)
            image = self.get_value(i, item_raw, IMAGE)
            sku = self.get_value(i, item_raw, PRODUCT_ID)
            if not sku:
                break
            link = self.get_value(i, item_raw, LINK)
            base_url = f"https://www.{self.store}.ca/"
            link = urljoin(base_url, link)
            ppq = self.get_value(i, item_raw, PACKAGE_SIZING)
            ppq = [ppq.replace("\xa0", "")] if ppq else [""]
            size = None
            regular_price, sale_price = self.parse_price(i, item_raw)
            aisle, category, subcategory = self.get_breadcrumbs(item_raw)
            sale_duration = None
            size_label = None
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
                Url=link,
                Size_Label=size_label,
                Store_id=self.store_id,
                UPC=None,
            ).model_dump_json()
            product_json = json.loads(product_model)
            self.outputs.append(product_json)

    def parsing_nodes(self, flattened_json: dict):
        """Parsing nodes from json"""
        num = 0
        nodes = []
        while True:
            num2 = 0
            parent_name = flattened_json.get(f"{NAVIGATION}.[{num}].displayName")
            if parent_name:
                while True:
                    json_node = flattened_json.get(
                        f"{NAVIGATION}.[{num}].childNodes.[{num2}].url"
                    )
                    if json_node:
                        nodes.append(json_node)
                    else:
                        break
                    num2 += 1
            else:
                break
            num += 1
        return nodes

    @retry(exc=httpx.ReadTimeout, times=5, delay=10)
    def get_category_nodes(self, category_node: str) -> List[str]:
        """Getting all nodes from one parent node"""
        params = deepcopy(config.PARAMS)
        headers = deepcopy(config.HEADERS)
        date_node = parse("today")
        if not date_node:
            return []
        date_str = date_node.strftime("%d%m%Y")
        params["fulfillmentInfo"]["date"] = date_str
        headers["Accept-Language"] = self.lang
        params["banner"] = self.store
        print(params)
        response = httpx.post(
            url=f"https://api.pcexpress.ca/pcx-bff/api/v2/listingPage/{category_node}",
            headers=headers,
            json=params,
            timeout=None,
            # proxy=self.proxy_string("ca"),
        )
        print(f"Parent node requests status: {response.status_code}")
        response.raise_for_status()
        json_data = response.json()
        flattened_json = json_flatten.flatten(json_data)
        nodes = self.parsing_nodes(flattened_json)
        return nodes

    @retry(times=5, delay=10)
    def scrape_one_page(self, node_id: str, page_num: int) -> bool:
        """Scrape items from one page"""
        params = deepcopy(config.PARAMS)
        headers = deepcopy(config.HEADERS)
        params["listingInfo"]["pagination"]["from"] = page_num
        params["banner"] = self.store
        date_node = parse("today")
        if not date_node:
            return False
        date_str = date_node.strftime("%d%m%Y")
        params["fulfillmentInfo"]["date"] = date_str
        headers["Accept-Language"] = self.lang
        response = httpx.post(
            url=f"https://api.pcexpress.ca/pcx-bff/api/v2/listingPage/{node_id}",
            headers=headers,
            json=params,
            # proxy=self.proxy_string("ca"),
        )
        print(f"Child node requests status: {response.status_code}")
        response.raise_for_status()
        json_data = response.json()
        flattened_json = json_flatten.flatten(json_data)
        self.parse_one_item(flattened_json)
        if flattened_json.get(HAS_MORE) != "True":
            return False
        return True

    def scrape_one_category(self, category: str) -> None:
        """Scraping items of a category"""
        print(f"Aisle: {category}")
        try:
            child_links: list[str] = self.get_category_nodes(category)
        except Exception as _:
            child_links = []

        for child_link in child_links:
            there_is_next_page = True
            page_num: int = 1
            while there_is_next_page:
                print(f"Child link: {child_link} | Page: {page_num}")
                node_id = child_link.split("/")[-1]
                there_is_next_page = self.scrape_one_page(node_id, page_num)
                page_num += 1
            if self.environment == "beta":
                break

    def start_scraping(self) -> None:
        """Start Iterating through all categories"""

        for category in self.categories:
            self.scrape_one_category(category)
