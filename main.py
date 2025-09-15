from src.application.service import Orchestrator


def main():
    print("Hello from retailstorescraper!")
    orchestator = Orchestrator()
    orchestator.main()


if __name__ == "__main__":
    main()
