"""Leaf-Line FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import plants, readings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Leaf-Line")

# Allows the web frontend (a plain static page, possibly opened via
# file:// or a different port) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plants.router)
app.include_router(readings.router)
