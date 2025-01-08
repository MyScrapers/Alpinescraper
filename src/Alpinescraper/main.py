"""Main entryppoint for the alpine scraper."""

import argparse
import logging
from typing import Any, Dict, Type

from Alpinescraper.common import pipeline, scraper

LOGGER = logging.getLogger(__name__)

SCRAPERS: Dict[str, Type[scraper.ScrapingOrchestrator]] = {
    "ascensionimmo": scraper.AscensionImmoOrchestrator,
    "acmimmobilier": scraper.AcmImmobilierOrchestrator,
    "agenceolivier": scraper.AgenceOlivierOrchestrator,
    "morzineimmo": scraper.MorzineImmorchestrator,
}


def webscrape_to_mongodb(
    orchestrator: Any, collection_name: str, nb_spider: int = 10, append: bool = False
) -> None:
    """Run a scraper and write the data in MongoDB."""
    LOGGER.info("Scraping with %i spiders for %s...", nb_spider, orchestrator.__name__)
    orchestrator = orchestrator(nb_spider=nb_spider)
    scraped_items = orchestrator.deploy_army()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items)
    pipe.write_mongodb(collection_name=collection_name, append=append)
    LOGGER.info("Scraping complete.")


def main_mongodb() -> None:
    """Main entrypoint for the application to write in MongoDB."""
    parser = argparse.ArgumentParser(description="Run the alpine scraper")
    parser.add_argument(
        "--scraper",
        type=str,
        choices=SCRAPERS.keys(),
        help="Name of the scraper to run",
        default="ascensionimmo",
    )
    parser.add_argument(
        "--nb_spider", type=int, help="Number of spiders to deploy", default=10
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        help="Collection filename to store the result in the MongoDB",
        nargs="?",
        const=1,
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append the data to the existing JSON file",
        default=False,
    )

    args = parser.parse_args()

    orchestrator: Type[scraper.ScrapingOrchestrator] = SCRAPERS[args.scraper]
    nb_spider: int = args.nb_spider
    collection_name: str = args.collection_name
    append: bool = args.append

    webscrape_to_mongodb(
        orchestrator=orchestrator,
        nb_spider=nb_spider,
        collection_name=collection_name,
        append=append,
    )


def webscrape_to_json(
    orchestrator: Any,
    nb_spider: int = 10,
    json_filename: str = "result.json",
    append: bool = False,
) -> None:
    """Run a scraper and write the data in a JSON file."""
    LOGGER.info("Scraping with %i spiders for %s...", nb_spider, orchestrator.__name__)
    orchestrator = orchestrator(nb_spider=nb_spider)
    scraped_items = orchestrator.deploy_army()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items)
    pipe.write_json(json_filename=json_filename, append=append)
    LOGGER.info("Scraping complete.")


def main_json() -> None:
    """Main entrypoint for the application to write in JSON."""
    parser = argparse.ArgumentParser(description="Run the alpine scraper")
    parser.add_argument(
        "--scraper",
        type=str,
        choices=SCRAPERS.keys(),
        help="Name of the scraper to run",
        default="ascensionimmo",
    )
    parser.add_argument(
        "--nb_spider", type=int, help="Number of spiders to deploy", default=1
    )
    parser.add_argument(
        "--json_filename",
        type=str,
        help="JSON filename to store the result",
        nargs="?",
        const=1,
        default="result.json",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append the data to the existing JSON file",
        default=False,
    )

    args = parser.parse_args()

    orchestrator: Type[scraper.ScrapingOrchestrator] = SCRAPERS[args.scraper]
    nb_spider: int = args.nb_spider
    json_filename: str = args.json_filename
    append: bool = args.append
    webscrape_to_json(
        orchestrator=orchestrator,
        nb_spider=nb_spider,
        json_filename=json_filename,
        append=append,
    )


if __name__ == "__main__":
    main_json()
