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
test:
  uv run pytest tests
