from enum import Enum
from src.presentation.cli import CliParser
from src.domain.workflows import BaseWorkflow


# 1: iga, 2: superc, 3: maxi, 4: metro, 5: provigo, 6: walmart
class StoreID(Enum):
    iga = 1
    superc = 2
    maxi = 3
    metro = 4
    provigo = 5
    walmart = 6


class Orchestrator:
    def __init__(self) -> None:
        self.cli = CliParser()

    def main(self):
        """Redirect the scrape to the appropriate scraper"""
        store = self.cli.store
        store_id = StoreID[f"{store}"].value
        flow = BaseWorkflow(
            store, store_id, self.cli.env, self.cli.script, self.cli.folder
        )
        flow.main()


if __name__ == "__main__":
    orchestator = Orchestrator()
    orchestator.main()
