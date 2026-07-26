"""Shared database session — single Base and engine for all modules."""
import os
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel_test.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    """Initialize database with tables and indexes."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create indexes
        from src.backend.shared.database_indexes import create_all_indexes
        db = SessionLocal()
        try:
            create_all_indexes(db)
            print("Database initialization completed successfully")
        except Exception as e:
            print(f"Warning: Could not create all indexes: {e}")
        finally:
            db.close()
            
    except OperationalError as e:
        print(f"Database initialization failed: {e}")
        raise


def get_db_connection() -> Generator:
    """Get database connection with connection pooling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
