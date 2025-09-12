from src.opengeodeweb_microservice.database.connection import get_session
from src.opengeodeweb_microservice.database.data import Data


def test_data_crud_operations():
    data = Data.create(geode_object="test_object", input_file="test.txt")
    assert data.id is not None
    session = get_session()
    session.commit()
    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.geode_object == "test_object"
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_additional_files():
    files = ["file1.txt", "file2.txt"]
    data = Data.create(geode_object="test_files", additional_files=files)
    session = get_session()
    session.commit()
    retrieved = Data.get(data.id)
    assert retrieved.additional_files == files
