import datetime
import json
from typing import TypedDict

import httpx
import pytest
from anycastd.healthcheck._cabourotte.result import Result, get_result
from pytest_mock import MockerFixture
from respx import MockRouter

CABOUROTTE_URL = "http://[::1]:9013"

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


class TestGetResult:
    """Test getting a result from the cabourotte API."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "name,url",
        [("example-http-check", CABOUROTTE_URL), ("example-dns-check", CABOUROTTE_URL)],
    )
    async def test_get_made_to_correct_url(
        self, name: str, url: str, respx_mock: MockRouter, mocker: MockerFixture
    ):
        """A GET request is made to the correct URL."""
        result_url = url + f"/result/{name}"
        mock_endpoint = respx_mock.get(result_url)
        mocker.patch("anycastd.healthcheck._cabourotte.result.Result.from_json")

        await get_result(name, url=url)

        request = mock_endpoint.calls.last.request
        assert request.method == "GET"
        assert request.url == result_url

    @pytest.mark.asyncio
    async def test_correct_result_returned(self, respx_mock):
        """The correct result corresponding to API data is returned."""
        json_data = json.dumps(example_result())
        name = "example-api"
        result_url = CABOUROTTE_URL + f"/result/{name}"

        mock_endpoint = respx_mock.get(result_url)
        mock_response = httpx.Response(status_code=200, content=json_data.encode())
        mock_endpoint.return_value = mock_response

        result = await get_result(name, url=CABOUROTTE_URL)

        assert result == Result.from_json(json_data)
