"""Route handlers for recording sensor readings."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import database, database_models, schemas

router = APIRouter()


@router.post("/sensorreading", response_model=schemas.SensorReadingResponse)
def create_sensor_reading(
    sensor_reading: schemas.SensorReadingCreate, db: Session = Depends(database.get_db)
):
    """Create a new sensor reading and return it with its assigned id."""
    db_reading = database_models.SensorReading(
        plant_id=sensor_reading.plant_id,
        moisture_reading=sensor_reading.moisture_reading,
        data_reading_date=datetime.now(timezone.utc),
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading
