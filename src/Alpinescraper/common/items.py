# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
"""Define the fields for the data scraped."""
import logging
from dataclasses import dataclass, field
from typing import Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class LuxuryestateItem:
    """Item type for the website Luxury Estate."""

    SPIDER: str = field()
    DATE: str = field()
    TITLE: str = field()
    PRICE: float = field()
    REFERENCE: str = field()
    URL: str = field()
    CURRENCY: Optional[str] = field(default=None)
    DESCRIPTION: Optional[str] = field(default=None)
    AGENCY: Optional[str] = field(default=None)
    ROOMS: Optional[float] = field(default=None)
    FLOOR: Optional[int] = field(default=None)
    BALCONY_COUNT: Optional[int] = field(default=None)
    BEDROOMS: Optional[float] = field(default=None)
    BATHROOMS: Optional[float] = field(default=None)
    EXTERNAL_SIZE: Optional[float] = field(default=None)
    SIZE: Optional[float] = field(default=None)
    EXTERIOR_AMENITIES: Optional[str] = field(default=None)
    INTERIOR_AMENITIES: Optional[str] = field(default=None)
    GARDEN: Optional[str] = field(default=None)
    HEATING: Optional[str] = field(default=None)
    STATUS: Optional[str] = field(default=None)
    ADDRESS: Optional[str] = field(default=None)
    HEATING_SOURCE: Optional[str] = field(default=None)
    VIEW: Optional[str] = field(default=None)
    TERRACE: Optional[bool] = field(default=None)
    ELEVATOR: Optional[bool] = field(default=None)
    YEAR_OF_CONSTRUCTION: Optional[int] = field(default=None)
    CAR_PARKING: Optional[bool] = field(default=None)
    PARKING_TYPE: Optional[str] = field(default=None)
