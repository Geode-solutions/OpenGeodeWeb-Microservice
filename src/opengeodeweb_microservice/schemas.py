import dataclasses
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


def format_dataclass(
    instance: "DataclassInstance", max_length: int = MAX_VALUE_LENGTH
) -> str:
    """Like repr(), but truncate every field value longer than max_length.

    Each truncated value is followed by its type and length.
    """
    fields = ", ".join(
        f"{field.name}={_format_value(getattr(instance, field.name), max_length)}"
        for field in dataclasses.fields(instance)
    )
    return f"{type(instance).__name__}({fields})"


def print_dataclass(instance: "DataclassInstance") -> None:
    sys.stdout.write(f"{format_dataclass(instance)}\n")
    sys.stdout.flush()


def get_schemas_dict(path: Path) -> dict[str, SchemaDict]:
    schemas_dict: dict[str, SchemaDict] = {}
    for json_file in path.glob("*.json"):
        with json_file.open() as file:
            schemas_dict[json_file.stem] = json.load(file)
    return schemas_dict


def load_schema(python_file: Path) -> dict[str, Any]:
    """Load the JSON route schema sitting next to a generated schema module."""
    with python_file.with_suffix(".json").open() as file:
        schema: dict[str, Any] = json.load(file)
    return schema


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
