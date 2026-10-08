import contextlib
from collections.abc import Generator
from pathlib import Path

import pytest

from opengeodeweb_microservice.database.connection import (
    close_database,
    get_session,
    init_database,
)
from opengeodeweb_microservice.database.data import Data

DB_PATH = Path(__file__).parent / "test_project.db"


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    init_database(DB_PATH)
    yield
    _cleanup_database(DB_PATH)


def _cleanup_database(db_path: Path) -> None:
    close_database()
    with contextlib.suppress(PermissionError):
        db_path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    with get_session() as session:
        session.query(Data).delete()
        session.commit()
        yield
        session.rollback()
