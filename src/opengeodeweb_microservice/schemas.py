import copy
import dataclasses
import functools
import json
import sys
from collections.abc import Sized
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dataclasses_json import DataClassJsonMixin

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

type SchemaDict = dict[str, str]

ERROR_SCHEMA_PATH = Path(__file__).parent / "error.json"
# Generated in each package by generate_schemas.js, see schema_types.js
SCHEMA_DEFINITIONS_FILENAME = "schema_definitions.json"


MAX_VALUE_LENGTH = 80


def _format_value(value: object, max_length: int) -> str:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return format_dataclass(value, max_length)
    text = repr(value)
    if len(text) <= max_length:
        return text
    details = type(value).__name__
    if isinstance(value, Sized):
        details += f", len={len(value)}"
    return f"{text[:max_length]}... ({details})"


def format_dataclass(instance: DataclassInstance, max_length: int = MAX_VALUE_LENGTH) -> str:
    """Like repr(), but truncate every field value longer than max_length.

    Each truncated value is followed by its type and length.
    """
    fields = ", ".join(
        f"{field.name}={_format_value(getattr(instance, field.name), max_length)}"
        for field in dataclasses.fields(instance)
    )
    return f"{type(instance).__name__}({fields})"


def print_dataclass(instance: DataclassInstance) -> None:
    sys.stdout.write(f"{format_dataclass(instance)}\n")
    sys.stdout.flush()


@functools.cache
def schema_definitions(directory: Path) -> dict[str, dict[str, Any]]:
    """Definitions of the shared schema types for the schemas of a directory.

    Read from the schema_definitions.json generated in its package, by the closest parent directory.
    """
    for parent in (directory, *directory.parents):
        definitions_file = parent / SCHEMA_DEFINITIONS_FILENAME
        if definitions_file.is_file():
            with definitions_file.open() as file:
                definitions: dict[str, dict[str, Any]] = json.load(file)
            return definitions
    return {}


def resolve_schema_types(schema: object, definitions: dict[str, dict[str, Any]]) -> object:
    """Give every schema titled after a shared type (e.g. {"title": "Point3D"}) its definition."""
    if isinstance(schema, list):
        return [resolve_schema_types(item, definitions) for item in schema]
    if not isinstance(schema, dict):
        return schema
    title = schema.get("title")
    if isinstance(title, str) and title in definitions:
        return {**schema, **copy.deepcopy(definitions[title])}
    return {key: resolve_schema_types(value, definitions) for key, value in schema.items()}


def _read_schema(json_file: Path) -> dict[str, Any]:
    with json_file.open() as file:
        schema = resolve_schema_types(json.load(file), schema_definitions(json_file.parent))
    if not isinstance(schema, dict):
        message = f"{json_file}: a schema must be a JSON object"
        raise TypeError(message)
    return schema


def get_schemas_dict(path: Path) -> dict[str, SchemaDict]:
    return {json_file.stem: _read_schema(json_file) for json_file in path.glob("*.json")}


def load_schema(python_file: Path) -> dict[str, Any]:
    """Load the JSON route schema sitting next to a generated schema module."""
    return _read_schema(python_file.with_suffix(".json"))


@dataclass(frozen=True)
class Route[ParamsT: DataClassJsonMixin, ResponseT: DataClassJsonMixin]:
    """Generated binding between a route schema, its request params and its success response."""

    schema: dict[str, Any]
    params: type[ParamsT]
    response: type[ResponseT]


@dataclass
class BinaryResponse(DataClassJsonMixin):
    """Response of a route streaming a file instead of JSON.

    Matches a schema with `"response": {"format": "binary"}`.
    """


@dataclass
class ErrorResponse(DataClassJsonMixin):
    """Body of every 4xx/5xx response, matches error.json."""

    code: int
    name: str
    description: str
