"""Main Description."""

import argparse
import logging

from Alpinescraper.common import luxuryestate, pipeline

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Main entrypoint for the application."""
    parser = argparse.ArgumentParser(description="Run the alpine scraper")
    parser.add_argument("nb_spider", type=int, help="Number of spider to deploy")
    parser.add_argument(
        "json_filename",
        type=str,
        help="Json filename to stores the result",
        nargs="?",
        const=1,
        default="result.json",
    )
    args = parser.parse_args()

    nb_spider = args.nb_spider
    json_filename = args.json_filename
    run_spider(nb_spider=nb_spider, json_filename=json_filename)


def run_spider(nb_spider: int, json_filename: str = "result.json") -> None:
    """Run you scraper."""
    LOGGER.info("Scraping with %i spiders...", nb_spider)
    luxuryestate_scraper = luxuryestate.Luxuryestate(nb_spider=nb_spider)
    scraped_items = luxuryestate_scraper.deploy_spider()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items, json_filename=json_filename)
    # pipe.write_json()
    pipe.write_mongodb("LUXURYESTATE")
    LOGGER.info("Scraping over.")


if __name__ == "__main__":
    main()
