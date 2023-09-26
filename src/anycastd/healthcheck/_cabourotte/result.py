import datetime

import httpx
from pydantic import BaseModel, Field


class Result(BaseModel):
    """The result of a healthcheck."""

    name: str
    summary: str
    success: bool
    timestamp: datetime.datetime = Field(alias="healthcheck-timestamp")
    message: str
    duration: int
    source: str

    @classmethod
    def from_json(cls, data: str | bytes | bytearray) -> "Result":
        """Create a result from JSON returned by the cabourotte API."""
        return cls.model_validate_json(data)


async def get_result(name: str, *, url: str) -> Result:
    """Get the result of a specific healthcheck.

    Arguments:
        name: The name of the healthcheck.
        url: The URL of the cabourotte API.

    Returns:
        The result of the healthcheck.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url}/result/{name}")
        response.raise_for_status()

    return Result.from_json(response.content)
