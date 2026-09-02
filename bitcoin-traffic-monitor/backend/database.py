"""
Database configuration and SQLAlchemy ORM session setup.
Supports PostgreSQL with fallback to SQLite for local development.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Environment variable configuration with local SQLite default fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# SQLite requires extra connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency that yields a SQLAlchemy database session
    and guarantees teardown after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
