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

    # Three-state classification against the plant's thresholds. This is
    # intentionally stateless (no dead zone): a two-threshold hysteresis
    # dead zone only works cleanly for a single binary flag - extending it
    # to three states would let a plant get stuck "overwatered" forever
    # with no path back to "happy" without first passing through
    # "needs_water", which is wrong. Sensor averaging on the device side
    # already smooths out most of the noise a dead zone would guard against.
    if sensor_reading.moisture_reading < plant.moisture_threshold_low:
        plant.needs_water = True
        plant.overwatered = False
    elif sensor_reading.moisture_reading > plant.moisture_threshold_high:
        plant.needs_water = False
        plant.overwatered = True
    else:
        plant.needs_water = False
        plant.overwatered = False

    db.commit()
    db.refresh(db_reading)
    return db_reading
