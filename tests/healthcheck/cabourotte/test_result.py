import datetime
import json
from typing import TypedDict

import pytest
from anycastd.healthcheck._cabourotte.result import Result

# The result of a healthcheck as returned by the cabourotte API.
_ResultData = TypedDict(
    "_ResultData",
    {
        "name": str,
        "summary": str,
        "success": bool,
        "healthcheck-timestamp": int,
        "message": str,
        "duration": int,
        "source": str,
    },
)


def example_result() -> _ResultData:
    """Return an example result."""
    return {
        "name": "example-api",
        "summary": "HTTP healthcheck on ::1:8080",
        "success": True,
        "healthcheck-timestamp": 1695648161,
        "message": "success",
        "duration": 1,
        "source": "configuration",
    }


@pytest.mark.parametrize("data", [example_result()])
def test_result_from_api_json(data: _ResultData):
    """Results can be created from JSON returned by the cabourotte API."""
    json_ = json.dumps(data)

    result = Result.from_json(json_)

    assert result.name == data["name"]
    assert result.summary == data["summary"]
    assert result.success == data["success"]
    assert result.timestamp == datetime.datetime.fromtimestamp(
        data["healthcheck-timestamp"], datetime.timezone.utc
    )
    assert result.message == data["message"]
    assert result.duration == data["duration"]
    assert result.source == data["source"]
