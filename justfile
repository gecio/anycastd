FRR_LATEST_MAJOR_VERSION := "10.1.0"

default: check-lockfile lint type-check test

# Check if the lockfile is up to date
check-lockfile:
  uv lock --locked

# Lint code and check formatting using ruff
lint +dirs="src tests":
  uv run ruff check {{ dirs }}
  uv run ruff format --check {{ dirs }}

# Validate static types using mypy
type-check +dirs="src":
  uv run mypy {{ dirs }}

# Run tests using pytest
test $COV=env("CI", "false") $FRR_VERSION=FRR_LATEST_MAJOR_VERSION:
  #!/usr/bin/env bash
  set -euxo pipefail

  args=()
  ( $COV == "true" ) && args+=( "--cov" )
  uv run pytest tests ${args[@]}

  if [ $COV = "true" ]; then
    uv run coverage xml
  fi
