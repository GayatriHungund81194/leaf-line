"""Route handlers for creating and retrieving plants."""

from fastapi import APIRouter, Depends
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
        moisture_threshold=plant.moisture_threshold,
        added_date=plant.added_date,
    )
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant
