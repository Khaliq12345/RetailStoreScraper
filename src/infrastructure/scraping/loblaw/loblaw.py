from src.infrastructure.scraping.loblaw.full import LoblawFullScraper
from src.infrastructure.scraping.loblaw.update import LoblawUpdateScraper


class LoblawScraper:
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
            return LoblawUpdateScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            ).main()
        elif self.script == "scrape":
            return LoblawFullScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            ).main()
