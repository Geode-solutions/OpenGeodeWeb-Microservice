import pytest
from src.opengeodeweb_microservice.database.session import get_session
from src.opengeodeweb_microservice.microservice.data import Data


def test_database_session_available(app_context):
    session = get_session()
    assert session is not None
    assert session.session is not None


def test_data_crud_operations(app_context, clean_database):
    data = Data.create(
        geode_object="test_object",
        input_file="test.txt",
        additional_files=["file1.txt", "file2.txt"],
    )
    assert data.id is not None
    assert data.geode_object == "test_object"
    assert data.additional_files == ["file1.txt", "file2.txt"]
    session = get_session()
    session.session.commit()
    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.geode_object == "test_object"
    assert retrieved.additional_files == ["file1.txt", "file2.txt"]
    non_existent = Data.get("fake_id")
    assert non_existent is None
