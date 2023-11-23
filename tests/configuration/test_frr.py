from pathlib import Path

from anycastd.configuration._frr import FRRPrefix


def test_from_simplified_format(example_networks):
    """The configuration can be created from it's simplified format.

    A prefix configuration can be created using it's simplified format, a single
    string containing the prefix.
    """
    data = str(example_networks)
    config = FRRPrefix.from_configuration(data)
    assert config == FRRPrefix(prefix=example_networks)


def test_from_expanded_format(example_networks):
    """The configuration can be created from it's full, expanded format.

    A prefix configuration can be created using it's full, expanded format, a
    dictionary containing the prefix as well as other optional options.
    """
    vrf = 42
    vtysh = Path("/vtysh")
    data = {"prefix": str(example_networks), "vrf": vrf, "vtysh": vtysh}

    config = FRRPrefix.from_configuration(data)

    assert config == FRRPrefix(prefix=example_networks, vrf=vrf, vtysh=vtysh)
