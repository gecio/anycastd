import pytest
from anycastd._executor import LocalExecutor

pytestmark = pytest.mark.integration


async def test_await_create_subprocess_exec_executes(tmp_path):
    """The subprocess is executed when the function is awaited."""
    executor = LocalExecutor()
    touch_file = tmp_path / "touch_file"

    process = await executor.create_subprocess_exec(
        "python3",
        "-c",
        f"from pathlib import Path; Path('{touch_file.as_posix()}').touch()",
    )
    await process.wait()

    assert touch_file.exists()


async def test_await_process_communicate_returns_stdout():
    """The communicate method of the returned process returns stdout."""
    executor = LocalExecutor()
    to_echo = "Hello, World!"

    process = await executor.create_subprocess_exec(
        "python3", "-c", f"print({to_echo!r})"
    )
    stdout, stderr = await process.communicate()

    assert stdout == to_echo.encode() + b"\n"
    assert stderr == b""


async def test_await_process_communicate_returns_stderr():
    """The communicate method of the returned process returns stderr."""
    executor = LocalExecutor()
    to_echo = "Hello, World!"

    process = await executor.create_subprocess_exec(
        "python3", "-c", f"import sys; print({to_echo!r}, file=sys.stderr)"
    )
    stdout, stderr = await process.communicate()

    assert stdout == b""
    assert stderr == to_echo.encode() + b"\n"
