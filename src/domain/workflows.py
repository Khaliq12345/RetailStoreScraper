from src.domain.scraper_factory import ScraperFactory

# TODO -> Setup a redis client and once the get all product has completed successfully, we cache the data and it will only expire after 24 hours


class BaseWorkflow:
    def __init__(
        self, store: str, store_id: int, environment: str, script: str, folder: str
    ) -> None:
        self.store = store
        self.store_id = store_id
        self.environment = environment
        self.script = script
        self.folder = folder

    def main(self) -> None:
        """Get the workflow to use"""
        factory = ScraperFactory(
            self.store, self.script, self.store_id, self.environment, self.folder
        )
        scraper = factory.get_scraper()
        if not scraper:
            print("Scraper not found")
            return None
        print("Starting the scraper")
        scraper.main()
