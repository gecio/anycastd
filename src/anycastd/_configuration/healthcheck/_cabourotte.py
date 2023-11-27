import datetime

from anycastd._configuration.sub import HealthcheckConfiguration

DEFAULT_URL = "http://127.0.0.1:9013"


class CabourotteHealthcheck(HealthcheckConfiguration):
    """The configuration for a Cabourotte healthcheck.

    Attributes:
        name: The name of the healthcheck.
        url: The URL of the cabourotte http endpoint.
        interval: The interval in seconds at which the healthcheck should be executed.
    """

    name: str
    url: str = DEFAULT_URL
    interval: datetime.timedelta = datetime.timedelta(seconds=5)
