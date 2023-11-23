from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from typing import Self

from pydantic_settings import BaseSettings


class FRRPrefix(BaseSettings):
    prefix: IPv4Network | IPv6Network
    vrf: int | None = None
    vtysh: Path = Path("/usr/bin/vtysh")

    @classmethod
    def from_configuration(cls, config: str | dict) -> Self:
        """Create an instance from the configuration format.

        The configuration can be provided in two formats, a simplified format
        containing only the prefix as a string, or a full format containing the
        prefix as well as other optional options.

        Args:
            config: The configuration for the prefix.

        Returns:
            A new FRRPrefix instance.
        """
        match config:
            case str():
                return cls.model_validate({"prefix": config})
            case dict():
                return cls.model_validate(config)
            case _:
                raise TypeError(f"Invalid configuration type {type(config)}")
