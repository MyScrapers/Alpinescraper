# mypy: disable-error-code="import-untyped"
"""Class definition of Luxuryestate deployer of spiders."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import numpy as np
import requests
from bs4 import BeautifulSoup, Tag

from Alpinescraper.common import luxuryestatespider
from Alpinescraper.common.items import LuxuryestateItem

LOGGER = logging.getLogger(__name__)


class Luxuryestate:
    """Class for scraping Luxuryestate."""

    def __init__(
        self,
        nb_spider: int,
        homepage: str = "https://www.luxuryestate.com/france/portes-du-soleil",
    ) -> None:
        """Initialize a Luxuryestate object."""
        self.nb_spider: int = nb_spider
        self.homepage: str = homepage

        self._urls: List[str] = self.fetch_luxury_estate_urls()
        self._army: List[luxuryestatespider.LuxuryestateSpider] = self.create_army()

    def fetch_luxury_estate_single_page_url(self, single_page: str) -> List[str]:
        """Retrieves the offer for a single page."""
        response = requests.get(single_page, timeout=300)
        if response.status_code != 200:
            LOGGER.warning("Failed to fetch page: %s", single_page)
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        urls = []
        for li_object in soup.select('li[data-role="go-to-detail"]'):
            link_tag = li_object.find("a", href=True)
            if isinstance(link_tag, Tag):  # Check if it's a Tag (not a NavigableString)
                href = link_tag.get("href")
                if isinstance(href, str):
                    urls.append(href)

        return urls

    def fetch_luxury_estate_urls(self) -> List[str]:
        """Return the URLs for all the offers."""
        page_number = 1
        all_urls = []
        page_url = f"{self.homepage}?pag={page_number}"
        response = requests.get(page_url, timeout=300)

        while response.status_code == 200:
            LOGGER.info("Fetching: %s", page_url)
            urls = self.fetch_luxury_estate_single_page_url(page_url)
            if not urls or page_number > 100:
                break
            all_urls.extend(urls)
            page_number += 1
            page_url = f"{self.homepage}?pag={page_number}"
            response = requests.get(page_url, timeout=300)

        return all_urls

    def create_army(self) -> List[luxuryestatespider.LuxuryestateSpider]:
        """Instantiate the spider army."""
        LOGGER.info("Creating : %i spider(s).", self.nb_spider)
        army = []
        for i in range(0, self.nb_spider):
            army.append(
                luxuryestatespider.LuxuryestateSpider(
                    name="luxuryestate_" + str(i + 1),
                    scrape_urls=list(np.array_split(self._urls, self.nb_spider)[i]),
                )
            )
        return army

    def deploy_spider(self) -> List[LuxuryestateItem]:
        """Run all spiders in parallel."""
        LOGGER.info("Deploying spider army.")
        retour = []
        with ThreadPoolExecutor(max_workers=self.nb_spider) as executor:

            # Submit spider.parse callables and store futures in a dictionary
            futures = {executor.submit(spider.parse): spider for spider in self._army}

            # Iterate over futures as they complete
            for future in as_completed(futures):
                spider = futures[future]
                result = future.result()
                LOGGER.info("Spider %s completed successfully", spider.name)
                retour.extend(result)
        return retour
