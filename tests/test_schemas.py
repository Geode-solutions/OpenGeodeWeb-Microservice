import json

import fastjsonschema  # type: ignore

from dataclasses import dataclass

from opengeodeweb_microservice.schemas import (
    ERROR_SCHEMA_PATH,
    ErrorResponse,
    format_dataclass,
)


def test_error_response_matches_error_schema() -> None:
    with open(ERROR_SCHEMA_PATH, "r") as file:
        validate = fastjsonschema.compile(json.load(file))
    validate(
        ErrorResponse(
            code=500, name="Internal Server Error", description="boom"
        ).to_dict()
    )


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
    assert text.startswith(
        "_Outer(name='short', content='xxxxxxxxxxxxxxxxxxx... (str, len=1000)"
    )
    assert "inner=_Inner(values=[0, 1, 2, 3, 4, 5, 6... (list, len=500))" in text
