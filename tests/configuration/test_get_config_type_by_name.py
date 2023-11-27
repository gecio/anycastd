"""Ensure the get_type_by_name function works as expected."""
import pytest
from anycastd._configuration import healthcheck, prefix
from anycastd._configuration.healthcheck import CabourotteHealthcheck
from anycastd._configuration.prefix import FRRPrefix


@pytest.mark.parametrize("name, type_", [("frrouting", FRRPrefix)])
def test_prefix_name_returns_correct_type(name: str, type_: type):
    """The correct prefix type is returned for a given name."""
    assert prefix.get_type_by_name(name) == type_  # type: ignore


@pytest.mark.parametrize("name, type_", [("cabourotte", CabourotteHealthcheck)])
def test_healthcheck_name_returns_correct_type(name: str, type_: type):
    """The correct healthcheck type is returned for a given name."""
    assert healthcheck.get_type_by_name(name) == type_  # type: ignore


def test_unknown_prefix_name_raises_error():
    """An unknown prefix name raises a ValueError."""
    name = "invalid"
    with pytest.raises(ValueError, match=f"Unknown prefix type: {name}"):
        prefix.get_type_by_name(name)  # type: ignore


def test_unknown_healthcheck_name_raises_error():
    """An unknown healthcheck name raises a ValueError."""
    name = "invalid"
    with pytest.raises(ValueError, match=f"Unknown healthcheck type: {name}"):
        healthcheck.get_type_by_name(name)  # type: ignore
