import os
import pytest
from src.opengeodeweb_microservice.database.connection import init_database, get_session
from src.opengeodeweb_microservice.database.data import Data


DB_PATH = os.path.join(os.path.dirname(__file__), "test_project.db")


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_database(DB_PATH)
    yield
    _cleanup_database(DB_PATH)


def _cleanup_database(db_path: str):
    try:
        session = get_session()
        session.close()
    except Exception:
        pass

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
def clean_database():
    session = get_session()
    session.query(Data).delete()
    session.commit()
    yield
    try:
        session.rollback()
    except Exception:
        pass
