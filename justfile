FRR_LATEST_MAJOR_VERSION := "9.1.0"

default: check-lockfile lint type-check test

# Check if the lockfile is up to date
check-lockfile:
  uv lock --locked

# Lint code and check formatting using ruff
lint:
  uv run ruff check src tests
  uv run ruff format --check src tests

# Validate static types using mypy
type-check:
  uv run mypy src

# Run tests using pytest
test $FRR_VERSION=FRR_LATEST_MAJOR_VERSION $COV=env("CI", "false"):
  #!/usr/bin/env bash
  set -euxo pipefail

  args=()
  ( $COV == "true" ) && args+=( "--cov" )
  uv run pytest tests ${args[@]}

  if [ -z ${CI} ]; then
    uv run coverge xml
  fi
