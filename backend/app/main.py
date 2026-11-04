"""Leaf-Line FastAPI application entry point."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import plants, readings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Leaf-Line")

app.include_router(plants.router)
app.include_router(readings.router)
