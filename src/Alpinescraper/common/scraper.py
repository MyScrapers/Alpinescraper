# mypy: disable-error-code="import-untyped"
"""Class definition to orchestrate the deployment of spiders."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import numpy as np
import requests
from bs4 import BeautifulSoup

from Alpinescraper.common.items import Item
from Alpinescraper.common.spiders import AscensionImmoSpider, Spider

LOGGER = logging.getLogger(__name__)


class ScrapingOrchestrator:
    """Class to orchestrate the scrapes."""

    def __init__(
        self,
        nb_spider: int,
        base_url: str,
    ) -> None:
        """Initialize a ScrapingOrchestrator object."""
        self.nb_spider: int = nb_spider
        self.base_url: str = base_url

        self._urls: List[str] = self.fetch_urls()
        self._army: List[Spider] = self.create_army()

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        raise NotImplementedError

    def create_army(self) -> List[Spider]:
        """Instantiate the spider army."""
        raise NotImplementedError

    def deploy_army(self) -> List[Item]:
        """Run all spiders in parallel."""
        LOGGER.info("Deploying spider army.")
        retour = []
        with ThreadPoolExecutor(max_workers=self.nb_spider) as executor:

            futures = {executor.submit(spider.deploy): spider for spider in self._army}

            # Iterate over futures as they complete
            for future in as_completed(futures):
                spider = futures[future]
                result = future.result()
                LOGGER.info("Spider %s completed successfully", spider.name)
                retour.extend(result)
        return retour


class AscensionImmoOrchestrator(ScrapingOrchestrator):
    """Class to orchestrate the deployment of AscensionImmo spiders."""

    def __init__(
        self,
        nb_spider: int,
        base_url: str = "https://www.ascension-immo.com/immobilier-morzine/vente/page",
    ) -> None:
        """Initialize a AscensionImmoOrchestrator object."""
        super().__init__(nb_spider, base_url)

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        page_number = 1
        urls: List[str] = []
        page_url = self.base_url + str(page_number) + "/"
        response = requests.get(page_url, timeout=300)
        soup = BeautifulSoup(response.content, "html.parser")

        while soup.find("a", class_="next page-numbers") is not None:
            LOGGER.info("Fetching: %s", page_url)
            soup = BeautifulSoup(response.content, "html.parser")
            for offer in soup.find_all("div", class_="property-item-content"):
                href = offer.find("a", href=True).get("href")
                if href:
                    urls.append(href)

            page_number += 1
            page_url = self.base_url + str(page_number) + "/"
            response = requests.get(page_url, timeout=300)

        return urls

    def create_army(self) -> List[Spider]:
        """Instantiate the spider army."""
        LOGGER.info("Creating %i AscensionImmoSpider(s).", self.nb_spider)
        army: List[Spider] = []
        for i in range(0, self.nb_spider):
            army.append(
                AscensionImmoSpider(
                    name="ascension_immo_" + str(i + 1),
                    urls=list(np.array_split(self._urls, self.nb_spider)[i]),
                )
            )
        return army
