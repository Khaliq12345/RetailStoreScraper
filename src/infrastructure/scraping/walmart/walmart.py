from src.infrastructure.scraping.walmart.full import WalmartFullScraper
from src.infrastructure.scraping.walmart.update import WalmartUpdateScraper


class WalmartScraper:
    def __init__(
        self, script: str, store: str, store_id: int, env: str, folder: str
    ) -> None:
        self.script = script
        self.store = store
        self.store_id = store_id
        self.env = env
        self.folder = folder

    def main(self):
        """Route to the right strategy based on the script"""
        if self.script == "update":
            return WalmartUpdateScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            ).main()
        elif self.script == "scrape":
            return WalmartFullScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            )
