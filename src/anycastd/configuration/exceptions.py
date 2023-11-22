from pathlib import Path


class ConfigurationError(Exception):
    """There was an error with the configuration file."""

    def __init__(self, path: Path, exc: Exception):
        msg = f"Could not read configuration file {path}: {exc}"
        super().__init__(msg)
