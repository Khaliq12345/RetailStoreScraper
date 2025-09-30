# from src.infrastructure.scraping.metro.full import WalmartFullScraper
from src.infrastructure.scraping.metro.update import (
    MetroUpdateScraper,
    SupercUpdateScraper,
)
from src.infrastructure.scraping.metro.full import MetroFullScraper, SupercFullScraper


class BaseScraper:
    def __init__(
        self, script: str, store: str, store_id: int, env: str, folder: str
    ) -> None:
        self.script = script
        self.store = store
        self.store_id = store_id
        self.env = env
        self.update_scraper = None
        self.full_scraper = None
        self.folder = folder

    def main(self):
        """Route to the right strategy based on the script"""
        if self.script == "update":
            return (
                self.update_scraper(
                    self.store, self.store_id, self.env, self.script, self.folder
                ).main()
                if self.update_scraper
                else None
            )
        elif self.script == "scrape":
            return (
                self.full_scraper(
                    self.store, self.store_id, self.env, self.script, self.folder
                ).main()
                if self.full_scraper
                else None
            )


class MetroScraper(BaseScraper):
    def __init__(
        self, script: str, store: str, store_id: int, env: str, folder: str
    ) -> None:
        super().__init__(script, store, store_id, env, folder)
        self.update_scraper = MetroUpdateScraper
        self.full_scraper = MetroFullScraper


class SupercScraper(BaseScraper):
    def __init__(
        self, script: str, store: str, store_id: int, env: str, folder: str
    ) -> None:
        super().__init__(script, store, store_id, env, folder)
        self.update_scraper = SupercUpdateScraper
        self.full_scraper = SupercFullScraper
