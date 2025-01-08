# mypy: disable-error-code="import-untyped"
"""Spiders definitions for the Alpine Scraper."""

import logging
import re
from datetime import date
from random import randint
from time import sleep
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, element

from .items import Item

LOGGER = logging.getLogger(__name__)


class Spider:
    """General Spider."""

    def __init__(self, name: str, urls: List[str]) -> None:
        """Constructor for a spider."""
        self.name: str = name
        self.urls: List[str] = urls

    def parse(self, url: str) -> Optional[Item]:
        """Parse the data for an offer."""
        raise NotImplementedError

    def deploy(self) -> List[Item]:
        """Deploy the spider."""
        items = []
        for url in self.urls:
            item = self.parse(url)
            sleep(randint(5, 15))
            if item:
                items.append(item)
        return items

    def clean_feature(self, feature: element.Tag) -> Optional[Tuple[str, str]]:
        """Clean a feature when they come in couple."""
        feature_data = feature.get_text(strip=True).split(":")
        if len(feature_data) == 2:
            feature_name = re.sub(r"^\s|\s$", "", feature_data[0])
            feature_value = re.sub(r"^\s|\s$", "", feature_data[1])
            return feature_name, feature_value
        return None


class AcmImmobilierSpider(Spider):
    """Class to scrap the website https://www.acm-immobilier.fr."""

    def __init__(self, urls: List[str], name: str = "acm_immobilier") -> None:
        """Constructor for the AcmImmobilier spider."""
        super().__init__(name, urls)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.conversion_args: Dict[str, str] = {
            "Surface habitable": "SIZE",
            "Surface terrain": "EXTERNAL_SIZE",
            "Nbre de pièces": "ROOMS",
            "Chambre": "BEDROOMS",
            "Nbre d'étages": "NB_FLOOR",
            "Exposition": "VIEW",
            "Année de construction": "YEAR_OF_CONSTRUCTION",
            "Parking": "PARKING",
            "Cave": "INTERIOR_AMENITIES",
            "Nbre de balcon": "BALCONY_COUNT",
            "Terrasse": "EXTERIOR_AMENITIES",
            "Nature chauffage": "HEATING",
            "Étage": "FLOOR",
            "Ascenseur": "ELEVATOR",
            "Type cuisine": "KITCHEN_TYPE",
            "Piscine": "POOL",
        }

    def parse(self, url: str) -> Optional[Item]:
        """Parse an offer."""
        try:
            response = requests.get(url, headers=self.headers, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.error("Failed to fetch page: %s, error: %s", url, exc)

        soup = BeautifulSoup(response.content, "html.parser")

        arg_dict = {}
        # Extract Item Fields
        arg_dict["TITLE"] = soup.find("title").get_text()
        arg_dict["DESCRIPTION"] = soup.find("div", id="description").get_text(
            strip=True
        )
        arg_dict["PRICE"] = soup.find("span", class_="prix").get_text(strip=True)
        arg_dict["REFERENCE"] = soup.find("span", class_="reference").get_text(
            strip=True
        )

        feature_list = soup.find("div", class_="critere-wrapper").find_all("div")
        if feature_list:
            bathrooms = 0
            for feature in feature_list:
                tup = feature.find_all("b")
                if not tup:
                    LOGGER.warning("No feature found for: %s", feature)
                    continue

                field_name = tup[0].get_text(strip=True)
                if field_name in self.conversion_args:
                    arg_dict[self.conversion_args[field_name]] = tup[1].get_text(
                        strip=True
                    )
                elif field_name in [
                    "Salle d'eau",
                    "Salle de bains",
                ]:  # Exception as differences is made in the website
                    bathrooms += int(tup[1].get_text(strip=True))
                else:
                    LOGGER.warning(
                        "Feature %s not found in conversion dict for url %s.",
                        field_name,
                        url,
                    )
            arg_dict["BATHROOMS"] = str(bathrooms)

        item = Item(
            SPIDER=self.name,
            AGENCY="ACM Immobilier",
            DATE=date.today().isoformat(),
            URL=url,
            **arg_dict
        )

        return item


class AgenceOlivierSpider(Spider):
    """Class to scrap the website https://www.agence-olivier.fr."""

    def __init__(self, urls: List[str], name: str = "agence_olivier") -> None:
        """Constructor for the AgenceOlivier spider."""
        super().__init__(name, urls)
        self.conversion_args: Dict[str, str] = {
            "Surface habitable": "SIZE",
            "Nombre de pièce": "ROOMS",
            "Chambres": "BEDROOMS",
            "Salle de bain": "BATHROOMS",
            "Parking": "PARKING",
            "Exposition": "VIEW",
            "Balcon": "BALCONY_COUNT",
            "Ascenseur": "ELEVATOR",
            "Ville": "LOCATION",
            "Etage": "FLOOR",
            "Charges de copropriété": "COOWNERSHIP",
            "Consommations énergétiques": "ENERGY_PERFORMANCE",
            "Émissions de GES": "GREENHOUSE_EMISSION",
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

        arg_dict = {}
        # Extract Item Fields
        arg_dict["TITLE"] = soup.find("div", class_="bloc_desc").find("h2").get_text()
        arg_dict["DESCRIPTION"] = (
            soup.find("div", class_="bloc_desc").find("p").get_text()
        )
        arg_dict["PRICE"] = soup.find("span", class_="prix").get_text()
        arg_dict["REFERENCE"] = soup.find("span", class_="ref").get_text()

        feature_list = soup.find("article", class_="info_plus_bien").find_all(
            "span", class_="detail"
        )
        if feature_list:
            try:
                for feature in feature_list.find_all("li"):
                    tup = self.clean_feature(feature)
                    if not tup:
                        LOGGER.warning("Feature not cleaned: %s", feature)
                        continue
                    if tup[0] in self.conversion_args:
                        arg_dict[self.conversion_args[tup[0]]] = tup[1]
                    else:
                        LOGGER.warning(
                            "Feature %s not found in conversion dict for url %s.",
                            tup[0],
                            url,
                        )
            except AttributeError:
                LOGGER.warning("No feature found for %s", url)

        item = Item(
            SPIDER=self.name,
            AGENCY="Agence Olivier",
            DATE=date.today().isoformat(),
            URL=url,
            **arg_dict
        )

        return item


class AscensionImmoSpider(Spider):
    """Class to scrap the website https://www.ascension-immo.com."""

    def __init__(self, urls: List[str], name: str = "ascension_immo") -> None:
        """Constructor for the AscensionImmo spider."""
        super().__init__(name=name, urls=urls)
        self.conversion_args: Dict[str, str] = {
            "Surface": "SIZE",
            "Chambre": "BEDROOMS",
            "Nombre de pièces": "ROOMS",
            "Nombre de piÃ¨ces": "ROOMS",
            "Nombre de pi√®ces": "ROOMS",
            "Nombre d'étages": "NB_FLOOR",
            "Nombre d'Ã©tages": "NB_FLOOR",
            "Nombre d'√©tages": "NB_FLOOR",
            "Salle de bains": "BATHROOMS",
            "Parking": "PARKING",
            "Copropriété": "COOWNERSHIP",
            "CopropriÃ©tÃ©": "COOWNERSHIP",
            "Copropri√©t√©": "COOWNERSHIP",
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
            soup.find("div", class_="property-heading").find("h1").get_text(strip=True)
        )
        arg_dict["PRICE"] = soup.find("span", class_="property-price").get_text(
            strip=True
        )
        arg_dict["REFERENCE"] = (
            soup.find("div", class_="property-id")
            .find("p", class_="property-info-value")
            .get_text(strip=True)
        )

        description = soup.find("div", class_="property-description")
        arg_dict["DESCRIPTION"] = (
            description.find("div", class_="ere-property-element").get_text(strip=True)
            if description and description.find("div", class_="ere-property-element")
            else None
        )

        property_type = soup.find("span", class_="property_type_cat")
        arg_dict["TYPE"] = property_type.get_text(strip=True) if property_type else None

        feature_list = soup.find("div", class_="property_type_inner")
        if feature_list:
            for feature in feature_list.find_all("li"):
                tup = self.clean_feature(feature)
                if not tup:
                    LOGGER.warning("Feature not cleaned: %s", feature)
                    continue
                if tup[0] in self.conversion_args:
                    arg_dict[self.conversion_args[tup[0]]] = tup[1]
                else:
                    LOGGER.warning(
                        "Feature %s not found in conversion dict for url %s.",
                        tup[0],
                        url,
                    )

        item = Item(
            SPIDER=self.name,
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
                next_span.get_text(strip=True).split("\n")[-1] if next_span else None
            )
        else:
            return_value = None

        return return_value


class MorzineImmoSpider(Spider):
    """Class to scrap the website https://www.morzine-immo.com/fr/."""

    def __init__(self, urls: List[str], name: str = "morzine-immo") -> None:
        """Constructor for the MorzineImmo spider."""
        super().__init__(name, urls)
        self.conversion_args: Dict[str, str] = {
            "Chambres": "BEDROOMS",
            "Salle de bain": "BATHROOMS",
            "Etages": "FLOOR",
            "Surface Habitable": "SIZE",
        }

    def parse(self, url: str) -> Optional[Item]:
        """Parse an offer."""
        try:
            response = requests.get(url, timeout=300)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Failed to fetch page: %s, error: %s", url, exc)
            return None

        soup = BeautifulSoup(response.content, "html5lib")

        arg_dict = {}
        # Extract Item Fields
        arg_dict["TITLE"] = soup.find("h1", class_="entry-title").get_text(strip=True)
        arg_dict["DESCRIPTION"] = (
            soup.find("h3", string="Description de la propriété")
            .find_next("p")
            .get_text(strip=True)
        )
        arg_dict["PRICE"] = soup.find("div", class_="price").get_text(strip=True)
        arg_dict["REFERENCE"] = soup.find(
            "li", string=lambda x: x and "Référence" in x
        ).get_text(strip=True)

        feature_list = soup.find("div", class_="property-meta")
        if feature_list:
            try:
                for feature in feature_list.find_all("li"):
                    tup = self.clean_feature(feature)
                    if tup:
                        arg_dict[tup[0]] = tup[1]

            except AttributeError:
                LOGGER.warning("No feature found for %s", url)

        item = Item(
            SPIDER=self.name,
            AGENCY="Morzine IMMO",
            DATE=date.today().isoformat(),
            URL=url,
            **arg_dict
        )

        return item

    def clean_feature(self, feature: element.Tag) -> Optional[Tuple[str, str]]:
        """Clean a feature for this specific scraper."""
        tmp_feat = feature.get_text(strip=True).lower()
        useless_feature = [
            "référence",
            "taxe",
            "sauna",
            "local",
            "salon",
            "buanderie",
            "cinéma",
            "cabine",
            "land",
            "bibliothèque",
            "séjour",
            "terrain",
            "entrée",
            "salle",
            "mezzanine",
            "commercial",
            "bureau",
            "piscine",
            "master",
            "dégagement",
            "studio",
            "sous-sol",
        ]

        for useless in useless_feature:
            if useless in tmp_feat:
                return None
        tup = super().clean_feature(feature)
        if tup:
            return (self.conversion_args[tup[0]], tup[1])

        tmp_convert_dict = {
            ("GARAGE", "1"): ["garage"],
            ("TERRACE", "1"): ["terrasse"],
            ("BALCONY_COUNT", "1"): ["balcon"],
            ("TYPE", "Appartement"): ["apartment", "apartment", "appartement"],
            ("TYPE", "Chalet"): ["chalet", "chalet"],
            ("GARDEN", "Yes"): ["jardin"],
            ("KITCHEN_TYPE", "Yes"): ["cuisine"],
            ("PARKING", "1"): ["parking"],
            ("INTERIOR_AMENITIES", ""): ["cave"],
        }

        for return_value, key_list in tmp_convert_dict.items():
            for key in key_list:
                if key in tmp_feat:
                    return return_value

        LOGGER.warning("Feature not cleaned: %s", feature)
        return None
