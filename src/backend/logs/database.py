"""Log module DB wiring — re-exports the shared Base/engine/session.

Mirrors src/backend/incidents/database.py exactly so every module talks to the
same single engine/metadata (FM-05: one source of truth for DB state).
"""
from src.backend.db import Base, SessionLocal, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

__all__ = ["Base", "SessionLocal", "engine", "get_db"]


def create_engine_and_session(url: str):
    eng = create_engine(url, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    session = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return eng, session
