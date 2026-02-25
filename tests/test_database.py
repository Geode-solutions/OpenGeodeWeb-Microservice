from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session


def test_data_crud_operations(clean_database: None) -> None:
    data = Data.create(
        geode_object="test_object",
        viewer_object="test_viewer",
        viewer_elements_type="test_type",
    )
    print("id", data.id, flush=True)
    assert data.id is not None
    assert isinstance(data.id, str)

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.geode_object == "test_object"
    assert retrieved.id == data.id
    non_existent = Data.get("fake_id")
    assert non_existent is None


def test_data_with_file_assignments(clean_database: None) -> None:
    data = Data.create(
        geode_object="geode_object",
        viewer_object="viewer_object",
        viewer_elements_type="test_type",
    )
    data_id = data.id
    data.native_file = "original.og_brep"
    data.viewable_file = "viewable.vtm"
    data.light_viewable_file = "light.vtp"

    with get_session() as session:
        session.add(data)
        session.commit()

    retrieved = Data.get(data_id)
    assert retrieved is not None
    assert retrieved.native_file == "original.og_brep"
    assert retrieved.viewable_file == "viewable.vtm"
    assert retrieved.light_viewable_file == "light.vtp"
    assert retrieved.geode_object == "geode_object"
