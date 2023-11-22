from ipaddress import IPv4Network, IPv6Network
from pathlib import Path

from pydantic_settings import BaseSettings


class FRRPrefix(BaseSettings):
    prefix: IPv4Network | IPv6Network
    vrf: int | None = None
    vtysh: Path = Path("/usr/bin/vtysh")
