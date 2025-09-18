from src.opengeodeweb_microservice.database.data import Data


def test_data_crud_operations(clean_database):
    data = Data.create(geode_object="test_object", input_file="test.txt")
    assert data.id is not None

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.geode_object == "test_object"
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_additional_files(clean_database):
    files = ["file1.txt", "file2.txt"]
    data = Data.create(geode_object="test_files", additional_files=files)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.additional_files == files
