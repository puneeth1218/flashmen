import os
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Configure a synchronous SQLAlchemy engine. Default to local SQLite database in data/ directory
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/alerts.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, index=True) # 'wallet' or 'ip'
    entity_id = Column(String, index=True)
    risk_score = Column(Float)
    confidence = Column(Float)
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency that yields a SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
