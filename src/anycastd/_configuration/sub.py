from pydantic import BaseModel


class HealthcheckConfiguration(BaseModel):
    """The configuration for a healthcheck."""


class PrefixConfiguration(BaseModel):
    """The configuration for a prefix."""
