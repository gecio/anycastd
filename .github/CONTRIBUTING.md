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

Ensure you have Python 3.11 or greater with recent versions of [uv] and [nox] in your environment.

## Coding Standards

All tests need to pass before a PR can be merged. Using [nox] to lint your code and run tests
before creating a PR is advised to avoid being reprimanded by CI.

```sh
$ nox
nox > Running session lint-3.11
...
nox > Ran multiple sessions:
nox > * lint-3.11: success
nox > * lint-3.12: skipped
nox > * test-3.11: success
nox > * test-3.12: skipped
```

Since some integration tests use real dependencies, docker is required to run them. If docker is not available in your environment, those tests will be skipped and only run in CI.

### Linting

`anycastd` uses [ruff] for uniform (black) formatting in addition to basic linting and enforcement of best practices,
as well as [mypy] for static type checks.

### Tests

- A high code coverage should be maintained. New functionality requires new tests.

- Write your asserts as `actual == expected` for convention.

  ```python
  assert result == expected
  ```

- Use the _Given When Then_ pattern.

  ```python
  # Given
  expected = 42  # setup required state
  # When
  result = f_being_tested()  # run the code being tested
  # Then
  assert result == expected  # confirm expectations
  ```

  When writing more complicated tests, use spacing to distinguish the different sections.

  ```python
  executor = Executor()
  to_echo = "Hello, World!"

  process = await executor.create_subprocess_exec(
      "echo", to_echo
  )
  stdout, stderr = await process.communicate()

  assert stdout == to_echo.encode() + b"\n"
  assert stderr == b""
  ```

[uv]: https://github.com/astral-sh/uv
[nox]: https://github.com/wntrblm/nox
[ruff]: https://github.com/astral-sh/ruff
[mypy]: https://github.com/python/mypy
