"""Define the process for the data scraped."""

import json
import logging
import os
import re
from dataclasses import asdict, fields, replace
from typing import Any, Callable, Dict, List, Optional

from pymongo import MongoClient
import ssl
from Alpinescraper.common.items import LuxuryestateItem

LOGGER = logging.getLogger(__name__)


class ItemPipeline:
    """Process the data scrapped."""

    def __init__(
        self,
        raw_item: List[LuxuryestateItem],
        json_filename: str = "RESULT.JSON",
    ) -> None:
        """Pipeline constructor."""
        self.raw_item: List[LuxuryestateItem] = raw_item
        self.json_filename: str = json_filename
        self.clean_item: List[LuxuryestateItem] = self.clean_raw_data()

    def serialize_int(self, string: str) -> Optional[int]:
        """Serialize string values to integer."""
        integer = int("".join(re.findall(r"[-+]?\d+", string.strip())))
        if not integer:
            return None
        return integer

    def serialize_float(self, string: str) -> Optional[float]:
        """Serialize string values to float."""
        float_val = float("".join(re.findall(r"[-+]?(?:\d*\.*\d+)", string.strip())))
        if not float_val:
            return None
        return float_val

    def serialize_bool(self, string: str) -> Optional[bool]:
        """Serialize string values to boolean."""
        value = string.strip().lower()
        true_values = ["yes", "true", "1"]
        false_values = ["no", "false", "0"]

        if value not in true_values + false_values:
            LOGGER.warning("value %s not recognised in bool serializer.", string)
            return None

        return value in true_values

    def serialize_string(self, input_string: str) -> Optional[str]:
        """Strip leading and trailing whitespace characters including newlines."""
        cleaned_string = input_string.strip()
        if not cleaned_string:
            return None
        return cleaned_string

    def apply_serializer(self, serializer: Callable[[str], Any], value: str) -> Any:
        """Apply the serializer to value based on the type define."""
        return serializer(value) if value is not None else None

    def clean_raw_data(self) -> List[LuxuryestateItem]:
        """Clean the data based on the type defined in the item."""
        clean_data: List[LuxuryestateItem] = []
        for item in self.raw_item:
            tmp_item = replace(item)
            for field in fields(item):
                field_value = getattr(item, field.name)
                if field.type in (Optional[float], float):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_float, field_value),
                    )
                elif field.type in (Optional[str], str):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_string, field_value),
                    )
                elif field.type in (Optional[int], int):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_int, field_value),
                    )
                elif field.type in (Optional[bool], bool):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_bool, field_value),
                    )
                else:
                    LOGGER.warning(
                        "Data types not recognised for %s and value %s.",
                        field.name,
                        field_value,
                    )
            clean_data.append(tmp_item)

        return clean_data

    def write_json(self) -> None:
        """Writes the data scraped in the json defined in attributes."""
        LOGGER.info("Writing data in : %s", self.json_filename)
        with open(self.json_filename, "w", encoding="utf-8") as file:
            json.dump(
                [asdict(item) for item in self.clean_item],
                file,
                ensure_ascii=False,
                indent=4,
            )

    def write_mongodb(self, collection: str) -> None:
        """Writes the data scraped in the json defined in attributes."""
        pwd = os.environ["MONGODB_PWD"]
        user = os.environ["MONGODB_USER"]
        mongo_database = os.environ["MONGODB_DATABASE"]
        LOGGER.info("Writing data in : %s", mongo_database)

        connection_string = f"mongodb+srv://{user}:{pwd}@cluster0.g0glf.mongodb.net/{mongo_database}?retryWrites=true&w=majority"
        client = MongoClient(connection_string, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
        try:
            client: MongoClient[Dict[str, Any]] = MongoClient(connection_string)
        except Exception as exception:  # pylint: disable=broad-exception-caught
            LOGGER.error("Couldn't connect to MongoDB: %s", exception)
        database_conection = client[mongo_database]
        tmp_collection = database_conection[collection]

        # Clean the collection
        tmp_collection.delete_many({})

        # Insert the new data
        try:
            tmp_collection.insert_many([asdict(item) for item in self.clean_item])
            LOGGER.info(
                "Data successfully written to MongoDB collection: %s", collection
            )
        except Exception as exception:  # pylint: disable=broad-exception-caught
            LOGGER.error("Error writing data to MongoDB: %s", exception)
