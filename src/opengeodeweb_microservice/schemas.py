import os
import glob
import json
import dataclasses
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from dataclasses_json import DataClassJsonMixin

type SchemaDict = dict[str, str]

ERROR_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "error.json")

ParamsT = TypeVar("ParamsT", bound=DataClassJsonMixin)
ResponseT = TypeVar("ResponseT", bound=DataClassJsonMixin)


MAX_VALUE_LENGTH = 80


def _format_value(value: Any, max_length: int) -> str:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return format_dataclass(value, max_length)
    text = repr(value)
    if len(text) <= max_length:
        return text
    details = type(value).__name__
    if hasattr(value, "__len__"):
        details += f", len={len(value)}"
    return f"{text[:max_length]}... ({details})"


def format_dataclass(instance: Any, max_length: int = MAX_VALUE_LENGTH) -> str:
    """Like repr(), but every field value longer than max_length is truncated and followed by its type and length."""
    fields = ", ".join(
        f"{field.name}={_format_value(getattr(instance, field.name), max_length)}"
        for field in dataclasses.fields(instance)
    )
    return f"{type(instance).__name__}({fields})"


def print_dataclass(instance: Any) -> None:
    print(format_dataclass(instance), flush=True)


def get_schemas_dict(path: str) -> dict[str, SchemaDict]:
    schemas_dict: dict[str, SchemaDict] = {}
    for json_file in glob.glob(os.path.join(path, "*.json")):
        filename = os.path.basename(json_file)
        with open(os.path.join(path, json_file), "r") as file:
            file_content = json.load(file)
            schemas_dict[os.path.splitext(filename)[0]] = file_content
    return schemas_dict


def load_schema(python_file: str) -> dict[str, Any]:
    """Load the JSON route schema sitting next to a generated schema module."""
    json_file = os.path.splitext(python_file)[0] + ".json"
    with open(json_file, "r") as file:
        schema: dict[str, Any] = json.load(file)
    return schema


@dataclass(frozen=True)
class Route(Generic[ParamsT, ResponseT]):
    """Generated binding between a route schema, its request params and its success response."""

    schema: dict[str, Any]
    params: type[ParamsT]
    response: type[ResponseT]


@dataclass
class BinaryResponse(DataClassJsonMixin):
    """Response of a route streaming a file (schema `"response": {"format": "binary"}`) instead of JSON."""


@dataclass
class ErrorResponse(DataClassJsonMixin):
    """Body of every 4xx/5xx response, matches error.json."""

    code: int
    name: str
    description: str
