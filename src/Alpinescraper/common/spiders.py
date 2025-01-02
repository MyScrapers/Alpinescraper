# mypy: disable-error-code="import-untyped"
"""Spiders definitions for the Alpine Scraper."""

import logging
import re
from datetime import date
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .items import Item

LOGGER = logging.getLogger(__name__)


class Spider:
    """General Spider."""

    def __init__(self, name: str, urls: List[str]) -> None:
        """Constructor for a spider."""
        self.name: str = name
        self.urls: List[str] = urls

    def parse(self, url: str) -> Optional[Item]:
        """Fetch the URL for the website."""
        raise NotImplementedError

    def deploy(self) -> List[Item]:
        """Fetch the URL for the website."""
        raise NotImplementedError


class AscensionImmoSpider(Spider):
    """Class to scrap the website https://www.ascension-immo.com."""

    def __init__(self, urls: List[str], name: str = "ascension-immo") -> None:
        """Constructor for the AscensionImmo spider."""
        super().__init__(name=name, urls=urls)
        self.conversion_args: Dict[str, str] = {
            "Surface": "SIZE",
            "Chambre": "BEDROOMS",
            "Nombre de pièces": "ROOMS",
            "Nombre d'étages": "NB_FLOOR",
            "Salle de bains": "BATHROOMS",
            "Parking": "PARKING",
            "Copropriété": "COOWNERSHIP",
            "Chauffage": "HEATING",
            "Garage": "GARAGE",
            "Exposition": "VIEW",
        }

    def parse(self, url: str) -> Optional[Item]:
        """Parse an offer."""
        try:
            response = requests.get(url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Failed to fetch page: %s, error: %s", url, exc)
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        arg_dict = {
            "ENERGY_PERFORMANCE": self.extract_feature_from_text(soup, "(DPE)"),
            "GREENHOUSE_EMISSION": self.extract_feature_from_text(soup, "(GES)"),
        }

        # Extract Item Fields
        arg_dict["TITLE"] = (
            soup.find("div", class_="property-heading").find("h1").text.strip()
        )
        arg_dict["PRICE"] = soup.find("span", class_="property-price").text.strip()
        arg_dict["REFERENCE"] = (
            soup.find("div", class_="property-id")
            .find("p", class_="property-info-value")
            .text.strip()
        )

        description = soup.find("div", class_="property-description")
        arg_dict["DESCRIPTION"] = (
            description.find("div", class_="ere-property-element").text.strip()
            if description and description.find("div", class_="ere-property-element")
            else None
        )

        property_type = soup.find("span", class_="property_type_cat")
        arg_dict["TYPE"] = property_type.text.strip() if property_type else None

        feature_list = soup.find("div", class_="property_type_inner")
        if feature_list:
            for feature in feature_list.find_all("li"):
                feature_data = feature.text.strip().split(":")
                if len(feature_data) == 2:
                    feature_name = re.sub(r"^\s|\s$", "", feature_data[0])
                    feature_value = re.sub(r"^\s|\s$", "", feature_data[1])
                    key = self.conversion_args.get(feature_name)
                    if key:
                        arg_dict[key] = feature_value

        item = Item(
            SPIDER="ascension_immo",
            AGENCY="Ascension Immobiler",
            DATE=date.today().isoformat(),
            URL=url,
            **arg_dict  # type: ignore[arg-type]
        )

        return item

    def extract_feature_from_text(
        self, soup: BeautifulSoup, text_arg: str
    ) -> Optional[str]:
        """Extract feature from text in a soup."""
        text_tag = soup.find("span", string=lambda text: text and text_arg in text)
        if text_tag:
            next_span = text_tag.find_next("span", class_="property_type_title")
            return_value: Optional[str] = (
                next_span.text.strip().split("\n")[-1] if next_span else None
            )
        else:
            return_value = None

        return return_value

    def deploy(self) -> List[Item]:
        """Deploy the spider."""
        items = []
        for url in self.urls:
            item = self.parse(url)
            if item:
                items.append(item)
        return items
