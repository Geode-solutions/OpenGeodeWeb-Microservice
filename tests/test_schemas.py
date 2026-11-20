import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import fastjsonschema

from opengeodeweb_microservice.schemas import (
    ERROR_SCHEMA_PATH,
    SCHEMA_DEFINITIONS_FILENAME,
    ErrorResponse,
    format_dataclass,
    get_schemas_dict,
    load_schema,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_error_response_matches_error_schema() -> None:
    with ERROR_SCHEMA_PATH.open() as file:
        validate = fastjsonschema.compile(json.load(file))
    validate(ErrorResponse(code=500, name="Internal Server Error", description="boom").to_dict())


@dataclass
class _Inner:
    values: list[int]


@dataclass
class _Outer:
    name: str
    content: str
    inner: _Inner


def test_format_dataclass_truncates_long_values() -> None:
    text = format_dataclass(
        _Outer(name="short", content="x" * 1000, inner=_Inner(values=list(range(500)))),
        max_length=20,
    )
    assert text.startswith("_Outer(name='short', content='xxxxxxxxxxxxxxxxxxx... (str, len=1000)")
    assert "inner=_Inner(values=[0, 1, 2, 3, 4, 5, 6... (list, len=500))" in text


def test_load_schema_resolves_the_shared_types(tmp_path: Path) -> None:
    geode_id = {"type": "string", "minLength": 36, "maxLength": 36}
    (tmp_path / SCHEMA_DEFINITIONS_FILENAME).write_text(json.dumps({"GeodeId": geode_id}))
    schemas_dir = tmp_path / "routes" / "schemas"
    schemas_dir.mkdir(parents=True)
    route = {
        "route": "components",
        "type": "object",
        "properties": {
            "geode_id": {"title": "GeodeId", "description": "Of the model"},
            "component_ids": {"type": "array", "items": {"title": "GeodeId"}},
            "other": {"title": "Other", "type": "string"},
        },
    }
    (schemas_dir / "components.json").write_text(json.dumps(route))

    schema = load_schema(schemas_dir / "components.py")

    properties = schema["properties"]
    assert properties["geode_id"] == {"title": "GeodeId", "description": "Of the model", **geode_id}
    assert properties["component_ids"]["items"] == {"title": "GeodeId", **geode_id}
    assert properties["other"] == {"title": "Other", "type": "string"}
    assert get_schemas_dict(schemas_dir) == {"components": schema}
    validate = fastjsonschema.compile(schema)
    validate({"geode_id": "0" * 36, "component_ids": [], "other": "x"})


def test_load_schema_without_definitions(tmp_path: Path) -> None:
    route = {"route": "name", "properties": {"name": {"title": "Name", "type": "string"}}}
    (tmp_path / "name.json").write_text(json.dumps(route))

    assert load_schema(tmp_path / "name.py") == route
