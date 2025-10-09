"""Database connection management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from .base import Base

DATABASE_FILENAME = "project.db"

engine = None
session_factory = None
scoped_session_registry = None


def init_database(db_path: str = DATABASE_FILENAME) -> None:
    global engine, session_factory, scoped_session_registry

    if engine is None:
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        print(f"Database engine created for {db_path}", flush=True)
        session_factory = sessionmaker(bind=engine)
        scoped_session_registry = scoped_session(session_factory)
        Base.metadata.create_all(engine)
        print(f"Database engine created DONE for {db_path}")
    else:
        print(f"Database engine already exists for {db_path}, reusing", flush=True)


def get_session() -> Session:
    if scoped_session_registry is None:
        raise RuntimeError()
    return scoped_session_registry()
