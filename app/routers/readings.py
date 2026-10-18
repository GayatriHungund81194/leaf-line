"""Route handlers for recording sensor readings."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import database, database_models, schemas

router = APIRouter()


@router.post("/sensorreading", response_model=schemas.SensorReadingResponse)
def create_sensor_reading(
    sensor_reading: schemas.SensorReadingCreate, db: Session = Depends(database.get_db)
):
    """Create a sensor reading and update the plant's watering state."""
    plant = db.get(database_models.Plant, sensor_reading.plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    db_reading = database_models.SensorReading(
        plant_id=sensor_reading.plant_id,
        moisture_reading=sensor_reading.moisture_reading,
        data_reading_date=datetime.now(timezone.utc),
    )
    db.add(db_reading)

    # Hysteresis: only flip needs_water when the reading clearly crosses
    # one of the two thresholds. Inside the dead zone, leave it as-is.
    if sensor_reading.moisture_reading < plant.moisture_threshold_low:
        plant.needs_water = True
    elif sensor_reading.moisture_reading > plant.moisture_threshold_high:
        plant.needs_water = False

    db.commit()
    db.refresh(db_reading)
    return db_reading
