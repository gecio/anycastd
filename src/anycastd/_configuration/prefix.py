from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from typing import Literal, TypeAlias

from anycastd._configuration.sub import SubConfiguration
from anycastd.prefix import VRF


class PrefixConfiguration(SubConfiguration):
    """A prefix configuration."""


class FRRPrefixConfiguration(PrefixConfiguration):
    """The configuration for a FRRouting prefix.

    Attributes:
        prefix: The prefix to advertise.
        vrf: The VRF to advertise the prefix in.
        vtysh: The path to the vtysh binary.
    """

    prefix: IPv4Network | IPv6Network
    vrf: VRF = None
    vtysh: Path = Path("/usr/bin/vtysh")


Name: TypeAlias = Literal["frrouting"]

_type_by_name: dict[Name, type[PrefixConfiguration]] = {
    "frrouting": FRRPrefixConfiguration,
}


def get_type_by_name(name: Name) -> type[PrefixConfiguration]:
    """Get a prefix configuration class by it's name as used in the configuration.

    Args:
        name: The name of the prefix type.

    Returns:
        The configuration class for the type of prefix.

    Raises:
        ValueError: There is no prefix type with the given name.
    """
    try:
        return _type_by_name[name]
    except KeyError as exc:
        raise ValueError(f"Unknown prefix type: {name}") from exc
