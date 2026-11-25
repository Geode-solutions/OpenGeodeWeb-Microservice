import json
from pathlib import Path
from typing import get_args

import pytest
from sqlalchemy import select

from opengeodeweb_microservice.database import data_types
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.data_types import (
    GeodeImageType,
    GeodeMeshType,
    GeodePolygonMeshType,
    GeodePolyhedronMeshType,
    InvalidGeodeObjectTypeError,
    ViewerObjectType,
    _flatten_literal_args,
    geode_object_type,
)

DATABASE_DIR = Path(data_types.__file__).parent
GEODE_ID = "01a08187-2c4c-7e64-85c5-52c3439f0626"


@pytest.mark.usefixtures("clean_database")
def test_data_crud_operations() -> None:
    data = Data.create(
        geode_id=GEODE_ID,
        geode_object_type="BRep",
        viewer_object_type="model",
        viewer_elements_type="test_type",
    )
    assert data.id is not None
    assert isinstance(data.id, str)
    assert len(data.id) == 32

    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert isinstance(retrieved, Data)
    assert retrieved.geode_object_type == "BRep"
    assert retrieved.geode_id == GEODE_ID
    assert retrieved.id == data.id
    non_existent = Data.get("fake_id")
    assert non_existent is None


@pytest.mark.usefixtures("clean_database")
def test_data_with_file_assignments() -> None:
    data = Data.create(
        geode_id=GEODE_ID,
        geode_object_type="BRep",
        viewer_object_type="model",
        viewer_elements_type="test_type",
    )
    data_id = data.id
    data.native_file = "native.og_brep"
    data.viewable_file = "viewable.vtm"
    data.light_viewable_file = "light.vtp"

    with get_session() as session:
        session.add(data)
        session.commit()

    retrieved = Data.get(data_id)
    assert retrieved is not None
    assert retrieved.native_file == "native.og_brep"
    assert retrieved.viewable_file == "viewable.vtm"
    assert retrieved.light_viewable_file == "light.vtp"
    assert retrieved.geode_object_type == "BRep"


@pytest.mark.usefixtures("clean_database")
def test_data_geode_id_is_not_unique() -> None:
    first = Data.create(
        geode_id=GEODE_ID,
        geode_object_type="BRep",
        viewer_object_type="model",
        viewer_elements_type="test_type",
    )
    second = Data.create(
        geode_id=GEODE_ID,
        geode_object_type="BRep",
        viewer_object_type="model",
        viewer_elements_type="test_type",
    )
    assert first.id != second.id
    session = get_session()
    rows = session.scalars(select(Data).where(Data.geode_id == GEODE_ID)).all()
    assert {row.id for row in rows} == {first.id, second.id}


@pytest.mark.usefixtures("clean_database")
@pytest.mark.parametrize("image_type", ["RasterImage2D", "RasterImage3D"])
def test_data_image_viewer_object_type(image_type: GeodeImageType) -> None:
    data = Data.create(
        geode_id=GEODE_ID,
        geode_object_type=image_type,
        viewer_object_type="image",
        viewer_elements_type="default",
    )
    retrieved = Data.get(data.id)
    assert retrieved is not None
    assert retrieved.viewer_object_type == "image"
    assert retrieved.geode_object_type == image_type


@pytest.mark.parametrize("image_type", ["RasterImage2D", "RasterImage3D"])
def test_image_types_are_geode_object_types(image_type: str) -> None:
    assert geode_object_type(image_type) == image_type
    assert image_type in get_args(GeodeImageType)
    assert image_type not in get_args(GeodePolygonMeshType)
    assert image_type not in get_args(GeodePolyhedronMeshType)
    assert image_type not in _flatten_literal_args(GeodeMeshType)


def test_invalid_geode_object_type() -> None:
    with pytest.raises(InvalidGeodeObjectTypeError):
        geode_object_type("RasterImage4D")


def test_viewer_object_types_start_with_image() -> None:
    assert get_args(ViewerObjectType) == ("image", "mesh", "model")


def test_generated_data_types_have_image() -> None:
    values = json.loads((DATABASE_DIR / "data_types.json").read_text())
    assert values["GeodeImageType"] == ["RasterImage2D", "RasterImage3D"]
    assert values["ViewerObjectType"] == ["image", "mesh", "model"]
    assert values["GeodeObjectType"][:2] == ["RasterImage2D", "RasterImage3D"]
    assert "RasterImage2D" not in values["GeodePolygonMeshType"]
    assert "RasterImage3D" not in values["GeodePolyhedronMeshType"]
    declarations = (DATABASE_DIR / "data_types.d.ts").read_text()
    assert 'export type GeodeImageType = "RasterImage2D" | "RasterImage3D";' in declarations
    assert (
        "export type GeodeObjectType = GeodeImageType | GeodeMeshType | GeodeModelType;"
        in declarations
    )
    assert 'export type ViewerObjectType = "image" | "mesh" | "model";' in declarations
