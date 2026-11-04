"""Pydantic schemas for the Leaf-Line API's request/response payloads."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class PlantCategories(str, Enum):
    """Supported plant categories, used to pick sensible moisture defaults."""

    AEROIDS = 'aeroids'
    SUCCULENTS = 'succulents'
    MARANTACEAE = 'marantaceae'
    BEGONIA =  'begonia'
    FERNS = 'ferns'

class PlantCreate(BaseModel):
    """Fields a client supplies when registering a new plant."""

    name: str
    category: PlantCategories
    quantity: int
    moisture_threshold_low: float
    moisture_threshold_high: float
    added_date: datetime

    class Config:
        """Allow building this schema from ORM model attributes."""

        from_attributes = True

class PlantResponse(BaseModel):
    """A stored plant, including the id assigned by the database."""

    id: int
    name: str
    category: PlantCategories
    quantity: int
    moisture_threshold_low: float
    moisture_threshold_high: float
    needs_water: bool
    added_date: datetime

    class Config:
        """Allow building this schema from ORM model attributes."""

        from_attributes = True

class SensorReadingCreate(BaseModel):
    """Fields a sensor device supplies when reporting a moisture reading."""

    plant_id: int
    moisture_reading: float

    class Config:
        """Allow building this schema from ORM model attributes."""

        from_attributes = True

class SensorReadingResponse(BaseModel):
    """A stored sensor reading, including its id and server-stamped time."""

    id: int
    plant_id: int
    moisture_reading: float
    data_reading_date: datetime

    class Config:
        """Allow building this schema from ORM model attributes."""

        from_attributes = True

class PlantStatus(BaseModel):
    """Whether a plant currently needs water, based on its latest reading."""

    plant_id: int
    name: str
    latest_moisture: Optional[float] = None
    needs_water: Optional[bool] = None
    moisture_threshold_low: Optional[float] = None
    moisture_threshold_high: Optional[float] = None

    class Config:
        """Allow building this schema from ORM model attributes."""

        from_attributes = True
