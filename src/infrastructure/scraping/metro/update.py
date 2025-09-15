from selectolax.parser import HTMLParser
from src.domain.entities import ProductModel
from src.domain.scraper_strategy import UpdateScraperStrategy
from src.infrastructure.scraping.metro import config
import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class BaseUpdateScraper(UpdateScraperStrategy):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = None
        self.headers = None

    def parse_one_item(self, item_raw: Any) -> None:
        soup: HTMLParser = item_raw.get("soup", "")
        # brand
        brand_node = soup.css_first(".pi--brand")
        brand = " ".join(brand_node.text().split()).strip() if brand_node else ""
        # name
        name_node = soup.css_first(".pi--name")
        name = " ".join(name_node.text().split()).strip() if name_node else ""
        # size
        size_node = soup.css_first(".pi--weight")
        size = " ".join(size_node.text().split()).strip() if size_node else ""
        size_value = size.split(" ")[0] or ""
        size_label_value = size.split(" ")[1] or ""
        # Img
        img_node = soup.css_first("#mob-img")
        img = img_node.attributes.get("src", "") if img_node else ""
        # Sale Duration
        sale_until_node = soup.css_first(".pricing__until-date")
        sale_until = (
            " ".join(sale_until_node.text().split()).strip()
            if sale_until_node
            else None
        )
        # Price per Quantity
        ppq_nodes = soup.css(".pricing__secondary-price span")
        ppq = [node.text().strip() for node in ppq_nodes] if ppq_nodes else []
        # Before Price
        bf_price_node = soup.css_first(".pricing__before-price")
        bf_price = (
            " ".join(bf_price_node.text().split()).strip().replace("Regular price", "")
            if bf_price_node
            else None
        )
        # Price
        price_node = soup.css_first(".pricing__sale-price")
        price = " ".join(price_node.text().split()).strip() if price_node else None
        sku = item_raw.get("product_id", "")
        item_url = item_raw.get("item_url")
        # Breadcumb
        # https://www.metro.ca/en/online-grocery/aisles/meat-poultry/beef-veal/steak-cuts/cap-off-ribsteaks-value-pack/p/236063
        bread_cumb_list = str(item_url).lower().split("aisles/") if item_url else None
        bread_cumb_list = bread_cumb_list[1].split("p/") if bread_cumb_list else None
        bread_cumb_list = bread_cumb_list[0].split("/") if bread_cumb_list else []
        aisle = category = sub_category = None
        match bread_cumb_list:
            case [a]:
                aisle = a if a != "" else None
            case [a, b]:
                aisle, category = a, b
            case [a, b, c, *rest]:
                aisle, category, sub_category = a, b, c
        parsed_item = ProductModel(
            Regular_Price=bf_price or price,
            Sale_Price=price,
            Price_Per_Quantity=ppq,
            #
            Aisle=aisle,
            Category=category,
            Sub_Category=sub_category,
            #
            Name=name,
            Sku=sku,
            Brand=brand,
            Size=size_value,
            Size_Label=size_label_value,
            Sale_Duration=sale_until,
            Image=img,
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
        response = httpx.get(
            f"{self.api_link}/{product_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        soup = HTMLParser(response.text)
        # print(soup.css_first("title").text())
        product = {}
        product["product_id"] = product_id
        product["item_url"] = item_url
        product["soup"] = soup
        self.parse_one_item(product)

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )


class MetroUpdateScraper(BaseUpdateScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.metro.ca/en/online-grocery/aisles/pantry/p"
        self.headers = config.metro_headers


class SupercUpdateScraper(BaseUpdateScraper):
    def __init__(
        self, store: str, store_id: int, environment: str, script: str
    ) -> None:
        super().__init__(store, store_id, environment, script)
        self.api_link = "https://api2.superc.ca/en/aisles/pantry/p"
        self.headers = config.superc_headers
