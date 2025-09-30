from src.infrastructure.scraping.loblaw.loblaw import LoblawScraper
from src.infrastructure.scraping.metro.metro import MetroScraper, SupercScraper
from src.infrastructure.scraping.walmart.walmart import WalmartScraper
from src.infrastructure.scraping.iga.iga import IgaScraper


class ScraperFactory:
    def __init__(
        self, store: str, script: str, store_id: int, env: str, folder: str
    ) -> None:
        self.store = store
        self.script = script
        self.store_id = store_id
        self.env = env
        self.folder = folder

    def get_scraper(self):
        scraper_map = {
            "walmart": WalmartScraper,
            "iga": IgaScraper,
            "superc": SupercScraper,
            "metro": MetroScraper,
            "maxi": LoblawScraper,
            "provigo": LoblawScraper,
        }

        scraper_class = scraper_map.get(self.store)
        if not scraper_class:
            raise ValueError(f"No scraper found for store: {self.store}")

        return scraper_class(
            self.script, self.store, self.store_id, self.env, self.folder
        )
