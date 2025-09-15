from copy import deepcopy
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import UpdateScraperStrategy

from src.infrastructure.scraping.iga import config
from typing import Any
import httpx
from concurrent.futures import ThreadPoolExecutor


class IgaUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)

    def first_where_price(self, prices_list, type: str) -> str | None:
        return next(
            (x.get("price") for x in prices_list if x.get("priceListType", "") == type),
            None,
        )

    def parse_one_item(self, item_raw: Any) -> None:
        propertyBag = item_raw.get("propertyBag")
        comparison_measure = (
            propertyBag.get("ComparisonMeasure") if propertyBag else None
        )
        comparison_measure_value = (
            comparison_measure.get("value") if comparison_measure else None
        )
        comparison_measure_value_enca = (
            comparison_measure_value.get("en-CA") if comparison_measure_value else None
        )
        prices_list = item_raw.get("prices")
        regular_price = None
        sale_price = None
        ppq_item = None
        if prices_list:
            regular_price = self.first_where_price(prices_list, "Regular")
            sale_price = self.first_where_price(prices_list, "Discount")
            ppq_item_price = self.first_where_price(prices_list, "Informational")
            ppq_item_unit = comparison_measure_value_enca
            ppq_item = (
                f"{ppq_item_price} / {ppq_item_unit}"
                if (ppq_item_price and ppq_item_unit)
                else None
            )
        ppq = [ppq_item] if ppq_item else []
        additional_info = (
            propertyBag.get("AdditionalInformation") if propertyBag else None
        )
        additional_info_value = (
            additional_info.get("value") if additional_info else None
        )
        additional_info_value_enca = (
            additional_info_value.get("en-CA") if additional_info_value else None
        )
        displayName = item_raw.get("displayName")
        displayName_enca = displayName.get("en-CA") if displayName else None
        name = (
            f"{additional_info_value_enca} {displayName_enca}"
            if (additional_info_value_enca and displayName_enca)
            else ""
        )
        sku = item_raw.get("sku", "")
        brand_name = propertyBag.get("BrandName") if propertyBag else None
        brand_name_value = brand_name.get("value") if brand_name else None
        brand_name_value_enca = (
            brand_name_value.get("en-CA") if brand_name_value else None
        )
        brand = brand_name_value_enca
        size_name = propertyBag.get("Size") if propertyBag else None
        size_name_value = size_name.get("value") if size_name else None
        size_name_value_enca = size_name_value.get("en-CA") if size_name_value else None
        size_name_value_enca_split = (
            size_name_value_enca.split(" ") if size_name_value_enca else []
        )
        size = size_name_value_enca_split[0] or None
        size_Label = size_name_value_enca_split[1] or None
        image_name = propertyBag.get("ProductImageFile") if propertyBag else None
        image_link = (
            f"https://sbs-prd-cdn-products.azureedge.net/media/image/product/en/medium/{image_name}".lower()
            if image_name
            else None
        )
        item_url = item_raw.get("item_url")
        parsed_item = ProductModel(
            Regular_Price=regular_price,
            Sale_Price=sale_price,
            Price_Per_Quantity=ppq,
            #
            Aisle=None,
            Category=None,
            Sub_Category=None,
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
        product["product_id"] = product_id
        product["item_url"] = item_url
        self.parse_one_item(product)
        # print(product["displayName"]["en-CA"])

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )
