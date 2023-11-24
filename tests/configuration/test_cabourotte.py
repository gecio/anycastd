import datetime

from anycastd._configuration.healthcheck import CabourotteHealthcheck


def test_from_simplified_format():
    """The configuration can be created from it's simplified format.

    A cabourotte healthcheck configuration can be created using it's simplified format,
    a string containing the name of the healthcheck.
    """
    name = "example-healthcheck"
    config = CabourotteHealthcheck.from_configuration(name)
    assert config == CabourotteHealthcheck(name=name)


def test_from_expanded_format():
    """The configuration can be created from it's full, expanded format.

    A cabourotte healthcheck configuration can be created using it's full,
    expanded format, a dictionary containing the name of the healthcheck
    as well as other optional options.
    """
    name = "example-healthcheck"
    url = "http://healthchecks.local"
    interval = 5
    data = {"name": name, "url": url, "interval": interval}

    config = CabourotteHealthcheck.from_configuration(data)
    assert config == CabourotteHealthcheck(
        name=name, url=url, interval=datetime.timedelta(seconds=5)
    )
