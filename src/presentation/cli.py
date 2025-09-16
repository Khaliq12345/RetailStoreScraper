from argparse import ArgumentParser


class CliParser:
    def __init__(self) -> None:
        """Parser the command line arguments"""
        args = ArgumentParser()
        args.add_argument("--store", type=str, required=True)
        args.add_argument("--script", required=True, choices=["update", "scrape"])
        args.add_argument("--env", type=str, required=True, choices=["prod", "beta"])
        args.add_argument("--folder", type=str, required=True, choices=["prod", "beta"])
        self.parser = args.parse_args()
        self.store = self.parser.store
        self.script = self.parser.script
        self.env = self.parser.env
        self.folder = self.parser.folder
