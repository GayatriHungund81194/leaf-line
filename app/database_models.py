"""SQLAlchemy table models for plants and their sensor readings."""

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Plant(Base):
    """A plant being monitored, with its watering threshold."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

    readings: Mapped[list["SensorReading"]] = relationship(back_populates="plant")


class SensorReading(Base):
    """A single moisture reading reported by a plant's sensor."""

    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    moisture_reading: Mapped[float] = mapped_column(Float, nullable=False)

    plant: Mapped["Plant"] = relationship(back_populates="readings")
