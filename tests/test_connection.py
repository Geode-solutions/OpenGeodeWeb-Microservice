import pytest
from src.opengeodeweb_microservice.database.session import (
    get_session, 
    get_database_connection
)
from src.opengeodeweb_microservice.database.connection import DatabaseConnection
from src.opengeodeweb_microservice.microservice.data import Data


def test_database_connection_basic(app_context):
    session = get_session()
    assert session is not None
    assert session.session is not None
    connection = get_database_connection()
    assert connection is not None


def test_data_crud_operations(app_context, clean_database):
    data = Data.create(
        geode_object="test_object",
        input_file="test.txt"
    )
    assert data.id is not None
    session = get_session()
    session.session.commit()
    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.geode_object == "test_object"
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_additional_files(app_context, clean_database):
    files = ["file1.txt", "file2.txt"]
    data = Data.create(
        geode_object="test_files",
        additional_files=files
    )
    session = get_session()
    session.session.commit()
    retrieved = Data.get(data.id)
    assert retrieved.additional_files == files