# mypy: disable-error-code="import-untyped"
"""Spider for website Luxury Estate."""

import logging
from datetime import date
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from .items import LuxuryestateItem

LOGGER = logging.getLogger(__name__)


class LuxuryestateSpider:
    """Spider to scrape the website Luxury Estate."""

    def __init__(  # pylint: disable=dangerous-default-value
        self,
        name: str = "luxuryestate",
        scrape_urls: List[str] = [],
    ) -> None:
        """Constructor for A LuxuryEstate spider."""
        self.name: str = name
        self.scrape_urls: List[str] = scrape_urls

    def parse_feature(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Scrape the data in the feature part of the website."""
        data = {}
        general_features = soup.find("div", class_="general-features")
        if general_features:
            features = general_features.find_all(
                lambda tag: tag.name == "div"
                and "item-inner" in tag.get("class", [])
                and "feat-item" in tag.get("class", [])
            )
            for feature in features:
                label = feature.find("span", class_="feat-label")
                value = feature.find("div", class_="single-value")
                label_text = label.get_text(strip=True) if label else None
                value_text = value.get_text(strip=True) if value else None

                if label_text and value_text:
                    data[label_text.replace(" ", "_").upper()] = value_text
        return data

    def parse_offer(self, url: str) -> LuxuryestateItem:
        """Extract the data from an offer."""
        response = requests.get(url, timeout=300)
        if response.status_code != 200:
            LOGGER.error(
                "Failed to fetch URL: %s with status code: %s",
                response.url,
                str(response.status_code),
            )
        soup = BeautifulSoup(response.content, "html.parser")
        price = soup.find(
            "div", class_="text-right price", attrs={"data-role": "property-price"}
        )
        currency = soup.find(
            "span",
            class_="selected value--text",
            attrs={"data-role": "property-currency-selected"},
        )
        description = soup.find("span", attrs={"data-role": "description-text-content"})
        agency = soup.find("div", class_="agency__name-container").find("a")

        data = self.parse_feature(soup)
        data["SPIDER"] = self.name
        data["URL"] = response.url
        data["DATE"] = date.today().strftime("%d-%m-%Y")
        data["TITLE"] = soup.find("h1", class_="serif-light title-property").get_text(
            strip=True
        )
        data["PRICE"] = price.get_text(strip=True) if price else None
        data["CURRENCY"] = currency.get_text(strip=True) if currency else None
        data["DESCRIPTION"] = description.get_text(strip=True) if description else None
        data["AGENCY"] = agency.get_text(strip=True) if agency else None

        LOGGER.info("Successfully parsed URL: %s", response.url)

        return LuxuryestateItem(**data)  # type: ignore[arg-type]

    def parse(self) -> List[LuxuryestateItem]:
        """Scrape all the url's stored in spider attributes."""
        item_list = []
        for url in self.scrape_urls:
            try:
                item_list.append(self.parse_offer(url))
                continue
            except Exception as exc:  # pylint: disable=broad-exception-caught
                LOGGER.error(
                    "Failed to fetch URL: %s with Exception: %s",
                    url,
                    str(exc),
                )
                continue
        return item_list
