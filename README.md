Using Layered Architecture


presentation/
   cli.py
   api.py                # (future-proof)

application/
   scraping_service.py   # Orchestrates workflows (full/update)
   commands.py           # FullScrapeCommand, UpdateScrapeCommand

domain/
   entities.py           # Product, Store, PriceChangeEvent
   workflows.py          # BaseWorkflow, FullScrapeWorkflow, UpdateScrapeWorkflow
   scraper_strategy.py   # Abstract scraper contract
   scraper_factory.py    # Chooses LoblawFullScraper, WalmartUpdateScraper
   repositories.py       # Abstract repo Interface

infrastructure/
   scraping/
      loblaw/
        full.py
        update.py
      walmart/
        full.py
        update.py
      metro/
        full.py
        update.py
      superc/
        full.py
        update.py
      iga/
        full.py
        update.py
    persistence/
        aws_repo.py
   config.py
