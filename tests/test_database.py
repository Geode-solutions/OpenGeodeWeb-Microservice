from opengeodeweb_microservice.database.data import Data


def test_data_crud_operations(clean_database):
    data = Data.create(
        geode_object="test_object",
        viewer_object="test_viewer",
        input_filename="test.txt",
        additional_filenames=[],
    )
    print("id", data.id, flush=True)
    assert data.id is not None
    assert isinstance(data.id, str)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.geode_object == "test_object"
    assert retrieved.input_filename == "test.txt"
    assert retrieved.id == data.id
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_additional_files(clean_database):
    files = ["file1.txt", "file2.txt"]
    data = Data.create(
        geode_object="test_files", viewer_object="test_viewer", additional_filenames=files
    )
    assert data.id is not None
    assert isinstance(data.id, str)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.additional_filenames == files
    assert retrieved.geode_object == "test_files"
