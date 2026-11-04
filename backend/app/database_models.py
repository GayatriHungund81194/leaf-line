"""SQLAlchemy table models for plants and their sensor readings."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Plant(Base):
    """A plant being monitored, with its watering threshold."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    moisture_threshold_low: Mapped[float] = mapped_column(Float, nullable=False)
    moisture_threshold_high: Mapped[float] = mapped_column(Float, nullable=False)
    needs_water: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    added_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    readings: Mapped[list["SensorReading"]] = relationship(back_populates="plant")


class SensorReading(Base):
    """A single moisture reading reported by a plant's sensor."""

    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    moisture_reading: Mapped[float] = mapped_column(Float, nullable=False)
    data_reading_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    plant: Mapped["Plant"] = relationship(back_populates="readings")
