from src.opengeodeweb_microservice.database.data import Data


def test_data_crud_operations(clean_database):
    data = Data.create(
        geode_object="test_object",
        viewer_object="test_viewer",
        input_file="test.txt",
        additional_files=[],
    )
    print("id", data.id, flush=True)
    assert data.id is not None
    assert isinstance(data.id, str)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.geode_object == "test_object"
    assert retrieved.input_file == "test.txt"
    assert retrieved.id == data.id
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_additional_files(clean_database):
    files = ["file1.txt", "file2.txt"]
    data = Data.create(
        geode_object="test_files", viewer_object="test_viewer", additional_files=files
    )
    assert data.id is not None
    assert isinstance(data.id, str)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.additional_files == files
    assert retrieved.geode_object == "test_files"
