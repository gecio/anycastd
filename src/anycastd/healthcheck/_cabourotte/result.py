import datetime

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
