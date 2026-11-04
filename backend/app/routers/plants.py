"""Route handlers for creating and retrieving plants."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import database, database_models, schemas

router = APIRouter()


@router.post("/plants", response_model=schemas.PlantResponse)
def create_plant(plant: schemas.PlantCreate, db: Session = Depends(database.get_db)):
    """Create a new plant and return it with its assigned id."""
    db_plant = database_models.Plant(
        name=plant.name,
        category=plant.category,
        quantity=plant.quantity,
        moisture_threshold_low=plant.moisture_threshold_low,
        moisture_threshold_high=plant.moisture_threshold_high,
        needs_water=False,
        added_date=plant.added_date,
    )
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant

@router.get("/plants/{plant_id}/status", response_model=schemas.PlantStatus)
def get_plant_status(
    plant_id: int, db: Session = Depends(database.get_db)
):
    """Report whether a plant needs water, based on its latest reading."""
    plant = db.get(database_models.Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    if not plant.readings:
        return schemas.PlantStatus(
            plant_id=plant.id,
            name=plant.name,
            needs_water=plant.needs_water,
            moisture_threshold_low=plant.moisture_threshold_low,
            moisture_threshold_high=plant.moisture_threshold_high,
        )

    latest_reading = max(plant.readings, key=lambda r: r.data_reading_date)

    return schemas.PlantStatus(
        plant_id=plant.id,
        name=plant.name,
        latest_moisture=latest_reading.moisture_reading,
        needs_water=plant.needs_water,
        moisture_threshold_low=plant.moisture_threshold_low,
        moisture_threshold_high=plant.moisture_threshold_high,
    )

@router.get("/plants", response_model=List[schemas.PlantResponse])
def list_plants(db: Session = Depends(database.get_db)):
    """List all plants in the database."""
    return db.query(database_models.Plant).all()
