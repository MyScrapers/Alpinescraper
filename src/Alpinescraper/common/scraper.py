# mypy: disable-error-code="import-untyped"
"""Class definition to orchestrate the deployment of spiders."""

import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Type
from urllib.parse import urljoin

import numpy as np
import requests
from bs4 import BeautifulSoup

from Alpinescraper.common.items import Item
from Alpinescraper.common.spiders import (
    AcmImmobilierSpider,
    AgenceOlivierSpider,
    AscensionImmoSpider,
    CimalpeSpider,
    MorzineImmoSpider,
    Spider,
)

LOGGER = logging.getLogger(__name__)


class ScrapingOrchestrator(ABC):
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

    @abstractmethod
    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        raise NotImplementedError

    @property
    @abstractmethod
    def spider_class(self) -> Type[Spider]:
        """Return the spider class specific to the orchestrator."""
        raise NotImplementedError

    def create_army(self) -> List[Spider]:
        """Instantiate the spider army."""
        LOGGER.info("Creating %i %s(s).", self.nb_spider, self.spider_class.__name__)
        army: List[Spider] = []
        for i in range(0, self.nb_spider):
            army.append(
                self.spider_class(
                    name=f"{self.spider_class.__name__.lower()}_{i + 1}",
                    urls=list(np.array_split(self._urls, self.nb_spider)[i]),
                )
            )
        return army

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


class AgenceOlivierOrchestrator(ScrapingOrchestrator):
    """Class to orchestrate the deployment of AgenceOlivier spiders."""

    def __init__(
        self,
        nb_spider: int,
        base_url: str = "https://www.agence-olivier.fr/acheter.html",
    ) -> None:
        """Initialize a AgenceOlivierOrchestrator object."""
        super().__init__(nb_spider, base_url)

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        urls: List[str] = []
        try:
            response = requests.get(self.base_url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.error("Failed to fetch page: %s, error: %s", self.base_url, exc)

        LOGGER.info("Fetching: %s", self.base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        for offer in soup.find_all(
            "div", class_="bloc_vente bloc_vente_0"
        ) + soup.find_all("div", class_="bloc_vente bloc_vente_1"):
            href = offer.find("a", href=True).get("href")
            if href:
                urls.append(href)
        return urls

    @property
    def spider_class(self) -> Type[AgenceOlivierSpider]:
        """Return the class of the spider used."""
        return AgenceOlivierSpider


class AcmImmobilierOrchestrator(ScrapingOrchestrator):
    """Class to orchestrate the deployment of AcmImmobilier spiders."""

    def __init__(
        self, nb_spider: int, base_url: str = "https://www.acm-immobilier.fr/fr/ventes"
    ) -> None:
        """Initialize a AcmImmobilierOrchestrator object."""
        self._headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        super().__init__(nb_spider, base_url)

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        urls: List[str] = []
        page_number = 1
        page_url = f"{self.base_url}/{page_number}"
        while True:
            try:
                response = requests.get(page_url, headers=self._headers, timeout=300)
                response.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.error("Failed to fetch page: %s, error: %s", page_url, exc)
                break

            soup = BeautifulSoup(response.content, "html.parser")

            LOGGER.info("Fetching: %s", page_url)
            for offer in soup.find_all("div", class_="filter-vignette"):
                relative_url = offer.find("a", class_="img_bien")["href"]
                if relative_url:
                    urls.append(urljoin(self.base_url, relative_url))

            pagination = soup.find("ul", class_="pagination center-align")
            if not pagination or not pagination.find("span", class_="waves-effect"):
                break
            page_number += 1
            page_url = f"{self.base_url}/{page_number}"

        return urls

    @property
    def spider_class(self) -> Type[AcmImmobilierSpider]:
        """Return the class of the spider used."""
        return AcmImmobilierSpider


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
        try:
            response = requests.get(page_url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.error("Failed to fetch page: %s, error: %s", page_url, exc)

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
            try:
                response = requests.get(page_url, timeout=300)
                response.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.error("Failed to fetch page: %s, error: %s", page_url, exc)

        return urls

    @property
    def spider_class(self) -> Type[AscensionImmoSpider]:
        """Return the class of the spider used."""
        return AscensionImmoSpider


class MorzineImmorchestrator(ScrapingOrchestrator):
    """Class to orchestrate the deployment of MorzineImmo spiders."""

    def __init__(
        self,
        nb_spider: int,
        base_url: str = "https://www.morzine-immo.com/fr/acheter/",
    ) -> None:
        """Initialize a MorzineImmorchestrator object."""
        super().__init__(nb_spider, base_url)

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        page_number = 1
        urls: List[str] = []
        page_url = self.base_url

        try:
            response = requests.get(self.base_url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.error("Failed to fetch page: %s, error: %s", self.base_url, exc)
        soup = BeautifulSoup(response.content, "html.parser")

        while soup.find("a", class_="next page-numbers") is not None:
            LOGGER.info("Fetching: %s", page_url)
            soup = BeautifulSoup(response.content, "html.parser")
            for offer in soup.find_all("article", class_="rental-property"):
                href = offer.find("a", href=True).get("href")
                if href:
                    urls.append(href)

            page_number += 1
            page_url = self.base_url + f"page/{page_number}/"
            try:
                response = requests.get(page_url, timeout=300)
                response.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.error("Failed to fetch page: %s, error: %s", page_url, exc)

        return urls

    @property
    def spider_class(self) -> Type[MorzineImmoSpider]:
        """Return the class of the spider used."""
        return MorzineImmoSpider


class CimalpesOrchestrator(ScrapingOrchestrator):
    """Class to orchestrate the deployment of Cimalpes spiders."""

    def __init__(
        self,
        nb_spider: int,
        base_url: str = "https://cimalpes.com/fr/recherche-immobilier/",
    ) -> None:
        """Initialize a CimalpesOrchestrator object."""
        super().__init__(nb_spider, base_url)

    def fetch_urls(self) -> List[str]:
        """Fetch the URL for the website."""
        page_number = 1
        urls: List[str] = []
        page_url = self.base_url

        try:
            response = requests.get(self.base_url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.error("Failed to fetch page: %s, error: %s", self.base_url, exc)
        soup = BeautifulSoup(response.content, "html.parser")

        while soup.find("a", class_="page-link btn btn-primary pointeur") is not None:
            LOGGER.info("Fetching: %s", page_url)
            soup = BeautifulSoup(response.content, "html.parser")
            for offer in soup.find_all("div", class_="col-sm-6 col-lg-4 py-4"):
                href = offer.find("a", href=True).get("href")
                if href:
                    urls.append(urljoin(self.base_url, href))

            page_number += 1
            page_url = (
                self.base_url + f"?&rtype=achat&page_nb={page_number}&chambre=-1/"
            )
            try:
                response = requests.get(page_url, timeout=300)
                response.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.error("Failed to fetch page: %s, error: %s", page_url, exc)

        return urls

    @property
    def spider_class(self) -> Type[CimalpeSpider]:
        """Return the class of the spider used."""
        return CimalpeSpider
