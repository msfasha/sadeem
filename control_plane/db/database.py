"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic_settings import BaseSettings

from db.models import Base


class DatabaseSettings(BaseSettings):
    """Database settings."""
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lakehouse_platform"

    class Config:
        env_prefix = "DB_"


settings = DatabaseSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database (create tables)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

