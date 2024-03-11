import asyncio
from ipaddress import IPv6Network
from pathlib import Path

from anycastd._executor import LocalExecutor
from anycastd.prefix._frrouting.exceptions import FRRCommandError
from anycastd.prefix._frrouting.main import FRRoutingPrefix
from structlog.testing import capture_logs


def test_repr(example_networks, example_vrfs):
    """The repr of a FRRouting prefix is correct."""
    vtysh = Path("/usr/bin/vtysh")
    executor = LocalExecutor()
    prefix = FRRoutingPrefix(
        example_networks,
        vrf=example_vrfs,
        vtysh=vtysh,
        executor=executor,
    )
    assert repr(prefix) == (
        f"FRRoutingPrefix(prefix={example_networks!r}, vrf={example_vrfs!r}, "
        f"vtysh={vtysh!r}, executor={executor!r})"
    )


def test_equal():
    """Two prefixes with the same attributes are equal."""
    prefix1 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    prefix2 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    assert prefix1 == prefix2


def test_non_equal():
    """Two prefixes with different attributes are not equal."""
    prefix1 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    prefix2 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="43", executor=LocalExecutor()
    )
    assert prefix1 != prefix2


async def test_denouncing_non_announced_logs_warning(mocker):
    """Denouncing a non-announced prefix logs a warning."""
    prefix = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    # Using stdout for the error is intentional, it is how the vtysh does it.
    exc = FRRCommandError(
        ["test command"], 1, stdout="Can't find static route specified", stderr=""
    )
    mocker.patch.object(prefix, "_get_local_asn")
    mocker.patch.object(prefix, "_run_vtysh_commands", side_effect=exc)

    with capture_logs() as logs:
        await prefix.denounce()

    assert logs[0]["event"] == "Attempted to denounce prefix that was not announced."
    assert logs[0]["log_level"] == "warning"
    assert logs[0]["prefix"] == str(prefix.prefix)
    assert logs[0]["prefix_type"] == "FRRoutingPrefix"
    assert logs[0]["prefix_vrf"] == prefix.vrf
    assert logs[0]["vtysh_path"] == str(prefix.vtysh)


async def test_running_vtysh_commands_creates_debug_log(mocker):
    """
    Running vtysh commands creates a debug log containing the commands that were run
    and the result of the vtysh subprocess used to run them.
    """
    commands = ["show", "ip", "bgp", "detail"]
    proc_pid = 42
    proc_returncode = 0
    proc_stdout = b"example stdout"
    proc_stderr = b""

    mock_proc = mocker.create_autospec(asyncio.subprocess.Process)
    mock_proc.pid = proc_pid
    mock_proc.returncode = proc_returncode
    mock_proc.communicate.return_value = (proc_stdout, proc_stderr)

    mock_executor = mocker.create_autospec(LocalExecutor)
    mock_executor.create_subprocess_exec.return_value = mock_proc
    prefix = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), executor=mock_executor
    )

    with capture_logs() as logs:
        await prefix._run_vtysh_commands(*commands)

    assert logs[0]["event"] == "Ran vtysh commands."
    assert logs[0]["log_level"] == "debug"
    assert logs[0]["prefix"] == str(prefix.prefix)
    assert logs[0]["prefix_type"] == "FRRoutingPrefix"
    assert logs[0]["prefix_vrf"] == prefix.vrf
    assert logs[0]["vtysh_path"] == str(prefix.vtysh)
    assert logs[0]["vtysh_commands"] == commands
    assert logs[0]["vtysh_pid"] == proc_pid
    assert logs[0]["vtysh_returncode"] == proc_returncode
    assert logs[0]["vtysh_stdout"] == proc_stdout.decode("utf-8")
    assert logs[0]["vtysh_stderr"] is None
