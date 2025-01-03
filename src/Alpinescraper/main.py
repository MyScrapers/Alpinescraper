"""Main Description."""

import argparse
import logging

from Alpinescraper.common import pipeline, scraper

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
    try:
        run_ascensionimmo(nb_spider=nb_spider, json_filename=json_filename, append=True)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.warning("Error %s while running the scraper AscensionImmo", exc)
    try:
        run_acmimmobilier(nb_spider=nb_spider, json_filename=json_filename, append=True)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.warning("Error %s while running the scraper AcmImmobilier", exc)
    try:
        run_agenceolivier(nb_spider=nb_spider, json_filename=json_filename, append=True)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.warning("Error %s while running the scraper AgenceOlivier", exc)


def run_ascensionimmo(
    nb_spider: int, json_filename: str = "ascension_immo.json", append: bool = False
) -> None:
    """Run you scraper."""
    LOGGER.info("Scraping with %i AscensionImmoSpider spiders...", nb_spider)
    orchestrator = scraper.AscensionImmoOrchestrator(nb_spider=nb_spider)
    scraped_items = orchestrator.deploy_army()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items)
    pipe.write_json(json_filename=json_filename, append=append)
    # pipe.write_mongodb("ASCENSIONIMMO")
    LOGGER.info("Scraping over.")


def run_acmimmobilier(
    nb_spider: int, json_filename: str = "acm_immobilier.json", append: bool = False
) -> None:
    """Run you scraper."""
    LOGGER.info("Scraping with %i AcmImmobilierSpider spiders...", nb_spider)
    orchestrator = scraper.AcmImmobilierOrchestrator(nb_spider=nb_spider)
    scraped_items = orchestrator.deploy_army()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items)
    pipe.write_json(json_filename=json_filename, append=append)
    # pipe.write_mongodb("ACMIMMOBILIER")
    LOGGER.info("Scraping over.")


def run_agenceolivier(
    nb_spider: int, json_filename: str = "agence_olivier.json", append: bool = False
) -> None:
    """Run you scraper."""
    LOGGER.info("Scraping with %i AgenceOlivierSpider spiders...", nb_spider)
    orchestrator = scraper.AgenceOlivierOrchestrator(nb_spider=nb_spider)
    scraped_items = orchestrator.deploy_army()
    pipe = pipeline.ItemPipeline(raw_item=scraped_items)
    pipe.write_json(json_filename=json_filename, append=append)
    # pipe.write_mongodb("AGENCEOLIVIER")
    LOGGER.info("Scraping over.")


if __name__ == "__main__":
    main()
