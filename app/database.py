"""SQLAlchemy engine, session factory, and declarative base for Leaf-Line."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Shared declarative base that all table models inherit from."""


engine = create_engine("sqlite:///leafline.db")

SessionLocal = sessionmaker(bind=engine)  # pylint: disable=invalid-name


def get_db():
    """Yield a database session, closing it when the caller is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
