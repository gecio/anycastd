class CabourotteCheckError(Exception):
    """An error occurred while running a Cabourotte check.

    Attributes:
        name: The name of the check.
        url: The URL used to request the check result.
    """

    name: str
    url: str

    def __init__(self, name: str, url: str, spec: str):
        self.name = name
        self.url = url
        msg = (
            f'An error occurred while requesting the check result for "{name}": {spec}.'
        )
        super().__init__(msg)


class CabourotteCheckNotFoundError(CabourotteCheckError):
    """The requested Cabourotte check does not exist."""

    def __init__(self, name: str, url: str):
        spec = "The check could not be found"
        super().__init__(name, url, spec)
