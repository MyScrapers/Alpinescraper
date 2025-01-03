"""Define the process for the data scraped."""

import json
import logging
import os
import re
from dataclasses import asdict, fields, replace
from typing import Any, Callable, Dict, List, Optional

from pymongo import MongoClient

from Alpinescraper.common.items import Item

LOGGER = logging.getLogger(__name__)


class ItemPipeline:
    """Process the data scrapped."""

    def __init__(
        self,
        raw_item: List[Item],
        json_filename: str = "RESULT.JSON",
    ) -> None:
        """Pipeline constructor."""
        self.raw_item: List[Item] = raw_item
        self.json_filename: str = json_filename
        self.clean_item: List[Item] = self.clean_raw_data()

    def serialize_int(self, field_name: str, raw_item: Item) -> Optional[int]:
        """Serialize string values to integer."""
        string = getattr(raw_item, field_name)
        tmp_string = "".join(re.findall(r"[-+]?\d+", string.strip()))
        try:
            integer = int(tmp_string) if tmp_string or len(tmp_string) != 0 else None
            return integer
        except ValueError:
            LOGGER.warning(
                "value '%s' not recognised in int serializer for %s (%s).",
                string,
                field_name,
                getattr(raw_item, "URL"),
            )
            return None

    def serialize_float(self, field_name: str, raw_item: Item) -> Optional[float]:
        """Serialize string values to float."""
        string = getattr(raw_item, field_name)
        tmp_string = "".join(re.findall(r"[-+]?(?:\d*\.*\d+)", string.strip()))
        try:
            float_val = (
                float(tmp_string) if tmp_string or len(tmp_string) != 0 else None
            )
            return float_val
        except ValueError:
            LOGGER.warning(
                "value '%s' not recognised in float serializer for %s (%s).",
                string,
                field_name,
                getattr(raw_item, "URL"),
            )
            return None

    def serialize_bool(self, field_name: str, raw_item: Item) -> Optional[bool]:
        """Serialize string values to boolean."""
        string = getattr(raw_item, field_name)
        value = string.strip().lower()
        true_values = ["yes", "true", "1", "oui"]
        false_values = ["no", "false", "0", "non"]

        if value not in true_values + false_values:
            LOGGER.warning(
                "value '%s' not recognised in bool serializer for %s (%s).",
                string,
                field_name,
                getattr(raw_item, "URL"),
            )
            return None

        return value in true_values

    def serialize_string(self, field_name: str, raw_item: Item) -> Optional[str]:
        """Remove all occurrences of whitespace characters including newlines and strip leading and trailing whitespace."""
        string = getattr(raw_item, field_name)
        cleaned_string = re.sub(r"\s+", " ", string).strip()
        if not cleaned_string:
            LOGGER.warning(
                "value '%s' not recognised in string serializer for %s (%s).",
                string,
                field_name,
                getattr(raw_item, "URL"),
            )
            return None
        return cleaned_string

    def apply_serializer(
        self, serializer: Callable[[str, Item], Any], field_name: str, raw_item: Item
    ) -> Any:
        """Apply the serializer to value based on the type define."""
        value = getattr(raw_item, field_name)
        if value is None:
            return None
        return serializer(field_name, raw_item)

    def clean_raw_data(self) -> List[Item]:
        """Clean the data based on the type defined in the item."""
        clean_data: List[Item] = []
        for item in self.raw_item:
            tmp_item = replace(item)
            for field in fields(item):
                if field.type in (Optional[float], float):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_float, field.name, item),
                    )
                elif field.type in (Optional[str], str):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_string, field.name, item),
                    )
                elif field.type in (Optional[int], int):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_int, field.name, item),
                    )
                elif field.type in (Optional[bool], bool):
                    setattr(
                        tmp_item,
                        field.name,
                        self.apply_serializer(self.serialize_bool, field.name, item),
                    )
                else:
                    LOGGER.warning(
                        "Data types not recognised for %s and value %s.",
                        field.name,
                        getattr(item, field.name),
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
