from ipaddress import IPv4Network, IPv6Network
from pathlib import Path

from anycastd._configuration.sub import PrefixConfiguration


class FRRPrefix(PrefixConfiguration):
    """The configuration for a FRRouting prefix.

    Attributes:
        prefix: The prefix to advertise.
        vrf: The VRF to advertise the prefix in.
        vtysh: The path to the vtysh binary.
    """

    prefix: IPv4Network | IPv6Network
    vrf: int | None = None
    vtysh: Path = Path("/usr/bin/vtysh")
