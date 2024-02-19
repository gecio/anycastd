#!/usr/bin/env python3
import sys

MIN_PYTHON_VERSION = (3, 11)


def _check_python_version() -> None:
    """Check that minimum Python version requirements are met."""
    if sys.version_info < MIN_PYTHON_VERSION:
        sys.exit(
            f"Python >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} "
            "is required to run anycastd."
        )


def run() -> None:
    _check_python_version()
    from anycastd._cli import app

    app()


if __name__ == "__main__":
    run()
