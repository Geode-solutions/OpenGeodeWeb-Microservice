import os
import pytest
from flask import Flask
from src.opengeodeweb_microservice.database.connection import init_database, get_session
from src.opengeodeweb_microservice.microservice.data import Data


@pytest.fixture(scope="session")
def app():
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{os.path.join(os.path.dirname(__file__), 'test_project.db')}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })
    with app.app_context():
        init_database(app, "test_project.db")
        yield app
        _cleanup_database()

def _cleanup_database():
    try:
        session = get_session()
        if session:
            session.close()
    except Exception:
        pass
    db_path = os.path.join(os.path.dirname(__file__), "test_project.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass


@pytest.fixture
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture
def clean_database(app_context):
    session = get_session()
    if session:
        session.query(Data).delete()
        session.commit()
    yield
    if session:
        try:
            session.rollback()
        except Exception:
            pass
