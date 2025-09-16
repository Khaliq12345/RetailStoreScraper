from src.infrastructure.scraping.iga.full import IgaFullScraper
from src.infrastructure.scraping.iga.update import IgaUpdateScraper


class IgaScraper:
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
            return IgaUpdateScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            ).main()
        elif self.script == "scrape":
            return IgaFullScraper(
                self.store, self.store_id, self.env, self.script, self.folder
            ).main()
