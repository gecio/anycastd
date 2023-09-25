import datetime
import json

import pytest
from anycastd.healthcheck._cabourotte.result import Result


@pytest.mark.parametrize(
    "name,summary,success,timestamp,message,duration,source",
    [
        (
            "example-api",
            "HTTP healthcheck on ::1:8080",
            True,
            1695648161,
            "success",
            1,
            "configuration",
        )
    ],
)
def test_result_from_api_json(  # noqa: PLR0913
    name: str,
    summary: str,
    success: bool,  # noqa: FBT001
    timestamp: int,
    message: str,
    duration: int,
    source: str,
):
    """Results can be created from JSON returned by the cabourotte API."""
    data = json.dumps(
        {
            "name": name,
            "summary": summary,
            "success": success,
            "healthcheck-timestamp": timestamp,
            "message": message,
            "duration": duration,
            "source": source,
        }
    )

    result = Result.from_json(data)

    assert result.name == name
    assert result.summary == summary
    assert result.success == success
    assert result.timestamp == datetime.datetime.fromtimestamp(
        timestamp, datetime.timezone.utc
    )
    assert result.message == message
    assert result.duration == duration
    assert result.source == source
