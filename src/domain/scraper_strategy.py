from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional
from src.domain.entities import ProductModel
from src.infrastructure.config.config import Config
from src.infrastructure.presisitence.aws_repo import AWS
import httpx
from func_retry import retry


class ScraperStragegy(ABC):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__()
        self.aws = AWS()
        self.workers = 1
        self.store = store
        self.store_id = store_id
        self.environment = environment
        self.script = script
        self.outputs = []
        self.lang = "en"
        self.folder = folder
        self.save_type = ""

    def clean_output_keys(self) -> list[dict]:
        print("Cleaning the outputs")
        cleaned_outputs = []
        for output in self.outputs:
            updated_json = {
                key.replace("_", " "): value for key, value in output.items()
            }
            cleaned_outputs.append(updated_json)
        self.outputs = cleaned_outputs
        return self.outputs

    def save_to_s3(self) -> None:
        """Send the output to s3 bucket"""
        print(f"Sending output to s3 using the {self.save_type} method")
        if self.save_type == "append":
            self.aws.append_item_to_s3_bucket(
                self.outputs,
                f"{self.store}_{self.lang}.json",
                "update",
                self.folder,
            )
        else:
            self.aws.send_items_to_s3_bucket(
                self.outputs,
                f"{self.store}_{self.lang}.json",
                "update",
                self.folder,
            )
        print("Data sent to s3")

    @abstractmethod
    def parse_one_item(self, item_raw: Any) -> Optional[ProductModel]:
        """Parse raw item"""
        pass

    @abstractmethod
    def start_scraping(self) -> None:
        """Start the scraping"""
        pass

    def main(self):
        """Scrape and save data to s3"""
        self.start_scraping()
        self.clean_output_keys()
        self.save_to_s3()


class UpdateScraperStrategy(ScraperStragegy, ABC):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.login_url = "https://prodapi.eezly.app/auth/login/"
        self.merged_store_url = (
            "https://prodapi.eezly.app/stores/import/merged-store-items-urls"
        )
        self.config = Config()
        self.access_token = self.get_eezly_access_token()
        self.product_links = []

    @abstractmethod
    def update_one_item(self, item_url: str) -> None:
        """Parse products"""
        pass

    def update_multiple_items(self):
        """Scrape multiple items"""
        with ThreadPoolExecutor(max_workers=self.workers) as worker:
            for item_url in self.product_links:
                worker.submit(
                    self.update_one_item,
                    item_url,
                )

    @retry(times=5, delay=5)
    def get_eezly_access_token(self) -> str:
        """Login into eezly and get the access token to authenticate other endpoints"""
        json_data = {
            "username": self.config.EEZLY_EMAIL,
            "password": self.config.EEZLY_PASSWORD,
            "fcm_token": "5DCDS1",
        }
        response = httpx.post(self.login_url, json=json_data, timeout=60)
        response.raise_for_status()
        json_data = response.json()
        access_token = json_data["access_token"]
        access_token = f"Bearer {access_token}"
        return access_token

    @retry(times=5, delay=5)
    def get_all_product_links(self, limit: int = 1000):
        """
        This extract product links from the eezly beta api
        store_id: The id of the store
        1: iga, 2: superc, 3: maxi, 4: metro, 5: provigo, 6: walmart
        """
        headers = {"Authorization": self.access_token}
        num = 1
        while True:
            print(f"Page: {num}")
            url = f"{self.merged_store_url}?storeId={self.store_id}&page={num}&no_of_records={limit}"
            response = httpx.get(url, headers=headers, timeout=None)
            response.raise_for_status()
            json_data = response.json()
            print(f"Total: {json_data['total']}")
            if json_data["total"] == 0:
                break
            if not json_data["data"]:
                break
            for x in json_data["data"]:
                self.product_links.append(x["url"])
            if self.environment == "beta":
                break
            num += 1
        return self.product_links

    def start_scraping(self):
        """Start interation through all the items"""
        self.get_all_product_links()
        print(f"Total product links - {len(self.product_links)}")
        self.update_multiple_items()


class FullScraperStrategy(ScraperStragegy, ABC):
    def __init__(
        self,
        store: str,
        store_id: int,
        environment: str,
        script: str,
        folder: str,
    ) -> None:
        super().__init__(store, store_id, environment, script, folder)
        self.config = Config()
