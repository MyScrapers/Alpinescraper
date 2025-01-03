# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
"""Define the fields for the data scraped."""
import logging
from dataclasses import dataclass, field
from typing import Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class Item:
    """Item type for the websites."""

    DATE: str = field()
    PRICE: float = field()
    REFERENCE: str = field()
    SPIDER: str = field()
    TITLE: str = field()
    URL: str = field()

    AGENCY: Optional[str] = field(default=None)
    COOWNERSHIP: Optional[str] = field(default=None)
    BALCONY_COUNT: Optional[int] = field(default=None)
    BATHROOMS: Optional[float] = field(default=None)
    BEDROOMS: Optional[float] = field(default=None)
    CURRENCY: Optional[str] = field(default=None)
    DESCRIPTION: Optional[str] = field(default=None)
    ELEVATOR: Optional[bool] = field(default=None)
    ENERGY_PERFORMANCE: Optional[str] = field(default=None)
    EXTERNAL_SIZE: Optional[float] = field(default=None)
    EXTERIOR_AMENITIES: Optional[str] = field(default=None)
    FLOOR: Optional[int] = field(default=None)
    GARAGE: Optional[int] = field(default=None)
    GARDEN: Optional[str] = field(default=None)
    GREENHOUSE_EMISSION: Optional[str] = field(default=None)
    HEATING: Optional[str] = field(default=None)
    INTERIOR_AMENITIES: Optional[str] = field(default=None)
    LOCATION: Optional[str] = field(default=None)
    NB_FLOOR: Optional[int] = field(default=None)
    PARKING: Optional[int] = field(default=None)
    ROOMS: Optional[float] = field(default=None)
    SIZE: Optional[float] = field(default=None)
    STATUS: Optional[str] = field(default=None)
    TERRACE: Optional[bool] = field(default=None)
    TYPE: Optional[str] = field(default=None)
    VIEW: Optional[str] = field(default=None)
    YEAR_OF_CONSTRUCTION: Optional[int] = field(default=None)
