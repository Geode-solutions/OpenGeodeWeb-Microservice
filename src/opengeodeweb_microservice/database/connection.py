"""Database connection management"""

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .base import Base

DATABASE_FILENAME = Path("project.db")

logger = logging.getLogger(__name__)


class DatabaseNotInitializedError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Database not initialized. Call init_database() first.")


@dataclass
class _DatabaseState:
    engine: Engine | None = None
    scoped_session_registry: scoped_session[Session] | None = None


_state = _DatabaseState()


def init_database(
    db_path: Path = DATABASE_FILENAME, *, create_tables: bool = True
) -> None:
    if _state.engine is not None:
        logger.info("Database engine already exists for %s, reusing", db_path)
        return

    _state.engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    logger.info("Database engine created for %s", db_path)
    _state.scoped_session_registry = scoped_session(sessionmaker(bind=_state.engine))
    if create_tables:
        Base.metadata.create_all(_state.engine)
        logger.info("Database tables created for %s", db_path)
    else:
        logger.info("Database connected (tables not created) for %s", db_path)


def close_database() -> None:
    """Release every session and connection so the database file can be replaced."""
    if _state.scoped_session_registry is not None:
        _state.scoped_session_registry.remove()
    if _state.engine is not None:
        _state.engine.dispose()
    _state.engine = None
    _state.scoped_session_registry = None


def get_session() -> Session:
    if _state.scoped_session_registry is None:
        raise DatabaseNotInitializedError
    return _state.scoped_session_registry()
