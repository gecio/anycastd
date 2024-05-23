# How To Contribute

Thank you for considering contributing to `anycastd`!
This document intends to make contribution more accessible while aligning expectations.
Please don't hesitate to open issues and PRs regardless if anything is unclear.

By contributing to `anycastd`, you agree that your code will be licensed under the terms of the [Apache-2.0 License](../LICENSE) without any additional terms or conditions.

## Getting Started

To gain an overview of `anycastd`, please read the [README](../README.md).

## General Guidelines

- Contributions of all sizes are welcome, including single line grammar / typo fixes.
- For new features, documentation and tests are a requirement.
- Please use appropriate PR titles as we squash on merge.
- Changes must pass CI. PRs with failing CI will be treated as drafts unless you explicitly ask for help.
- Simplicity is a core objective of `anycastd`. Please open an issue before working on a new feature to discuss it.

## Development Environment

### Devcontainer

For users of IDEs with support for devcontainers, it's usage is recommended.

### Other

Ensure you have Python 3.11 or greater with recent versions of [pdm] and [nox] in your environment.

## Coding Standards

`anycastd` uses [ruff] for uniform (black) formatting in addition to basic linting and enforcement of best practices,
as well as [mypy] for static type checks.

In addition to basic formatting and linting, a high code coverage should be maintained.
Since some integration tests use real dependencies, docker is required to run them. If
docker is not available in your environment, those tests will be skipped and only run in CI.

All tests need to pass before a PR can be merged. Using [nox] to lint your code and run tests
(excluding those that require external dependencies like docker) before creating a PR is advised to avoid being reprimanded by CI.

```sh
$ nox
nox > Running session ruff-3.11
...
nox > Ran multiple sessions:
nox > * ruff-3.11: success
nox > * ruff-3.12: skipped
nox > * mypy-3.11: success
nox > * mypy-3.12: skipped
nox > * lockfile-3.11: success
nox > * lockfile-3.12: skipped
nox > * pytest-3.11: success
nox > * pytest-3.12: skipped
```

[pdm]: https://github.com/pdm-project/pdm
[nox]: https://github.com/wntrblm/nox
[ruff]: https://github.com/astral-sh/ruff
[mypy]: https://github.com/python/mypy
