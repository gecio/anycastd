FRR_LATEST_MAJOR_VERSION := "10.1.0"

default: check-lockfile lint type-check test

# Check if the lockfile is up to date
check-lockfile:
    uv lock --locked

# Lint code and check formatting
lint +dirs="src tests": lint-justfile
    uv run ruff check {{ dirs }}
    uv run ruff format --check {{ dirs }}

lint-justfile:
    just --check --fmt --unstable

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

# Build sdist and wheel
build:
    #!/usr/bin/env bash
    set -euxo pipefail

    # Validate version in pyproject.toml matches that of the git tag if running in CI
    if [ ! -z ${CI+x} ]; then
        PROJECT_VERSION="$(grep -Po '(?<=^version = ").*(?=")' pyproject.toml)"
        GIT_TAG="$(git describe --exact-match --tags)"

        if [ ! $PROJECT_VERSION == ${GIT_TAG:1} ]; then
            echo Project version $PROJECT_VERSION does not match git tag $GIT_TAG
            exit 1
        fi
    fi

    uv build

# Bump our version
bump-version $VERSION: (_validate_semver VERSION)
    #!/usr/bin/env bash
    set -euxo pipefail

    test -z "$(git status --porcelain)" || (echo "The working directory is not clean"; exit 1)

    sed -i 's/^version = .*/version = "'$VERSION'"/g' pyproject.toml
    uv lock --offline

    git add pyproject.toml *.lock
    git commit -m "Bump version to v{{ VERSION }}"

# Validate a version against SemVer 
_validate_semver version:
    #!/usr/bin/env bash
    set -euxo pipefail
    if [[ ! "{{ version }}" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-((0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?(\+([0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*))?$ ]]; then
        echo Invalid SemVer {{ version }}
        exit 1
    fi
