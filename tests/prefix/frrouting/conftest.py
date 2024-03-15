import json
import re
import subprocess
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from ipaddress import IPv4Network
from pathlib import Path

import pytest
from anycastd.prefix import VRF

from tests.conftest import _IP_Prefix


def get_afi(prefix: _IP_Prefix) -> str:
    """Return the FRR string AFI for the given IP type."""
    return "ipv6" if not isinstance(prefix, IPv4Network) else "ipv4"


@dataclass
class Vtysh:
    """A wrapper for vtysh.

    Attributes:
        docker: The path to the docker executable.
        container: The name of the container to run vtysh in.
        configure_terminal: Whether to enter configure terminal mode.
        context: The configuration context to run commands in.
    """

    docker: Path = Path("/usr/bin/docker")
    container: str = "frrouting"
    configure_terminal: bool = False
    context: list[str] = field(default_factory=list)

    def __call__(
        self,
        command: str,
        *,
        configure_terminal: bool | None = None,
        context: list[str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a command and return the output.

        Arguments:
            command: The command to run.
            configure_terminal: Run the command in a configure terminal.
            context: Run the command in a specific context.
            check: Raise an exception if the command exits with a nonzero return code.

        Returns:
            The completed command.
        """
        configure_terminal = configure_terminal or self.configure_terminal

        vty_cmd = []
        if configure_terminal:
            vty_cmd.append("configure terminal")
        if context := context or self.context:
            vty_cmd.extend(context)
        vty_cmd.append(command)

        docker_cmd = ["exec", "-i", self.container, "vtysh", "-c", "\n".join(vty_cmd)]

        result = subprocess.run(
            [self.docker.as_posix(), *docker_cmd],
            capture_output=True,
            check=False,
            text=True,
        )

        if check:
            try:
                result.check_returncode()
            except subprocess.CalledProcessError as exc:
                msg = f"Failed to run command in {self}:\n"
                if result.stdout:
                    msg += f"stdout: {result.stdout}\n"
                if result.stderr:
                    msg += f"stderr: {result.stderr}\n"
                raise RuntimeError(msg) from exc

        return result

    def exit(self, *, all: bool = False) -> None:
        """Exit the current context.

        Arguments:
            all: Exit all contexts.
        """
        if all:
            self.context.clear()
        else:
            self.context.pop()


def watchfrr_all_daemons_up(vtysh: Vtysh) -> bool:
    """Return whether all FRR daemons are up.

    Parses the output of `show watchfrr` and returns whether all daemons are up.

    Starting with FRR 8.3, the output looks somewhat like this:
    ```
    watchfrr global phase: Idle
    Restart Command: "/usr/lib/frr/watchfrr.sh restart %s"
    Start Command: "/usr/lib/frr/watchfrr.sh start %s"
    Stop Command: "/usr/lib/frr/watchfrr.sh stop %s"
    Min Restart Interval: 60
    Max Restart Interval: 600
    Restart Timeout: 20
     zebra                Up
     bgpd                 Up
     staticd              Up
    ```
    """
    re_daemon_status = re.compile(
        r"^\s{2}(?P<daemon>\w+)\s+(?P<status>\w+)$", re.MULTILINE
    )
    watchfrr_status = vtysh("show watchfrr").stdout
    return all(
        "Up" in daemon[1] for daemon in re_daemon_status.findall(watchfrr_status)
    )


@pytest.fixture
def frr_container(docker_services, docker_compose_project_name) -> str:
    """Create the FRR container and return its name.

    Spins up the FRR container using the docker_services fixture from
    pytest-docker, waits for all FRR services to be ready, and returns the name
    of the container.
    """
    name = f"{docker_compose_project_name}-frrouting-1"

    vtysh = Vtysh(container=name)
    docker_services.wait_until_responsive(
        timeout=60,
        pause=0.1,
        check=lambda: watchfrr_all_daemons_up(vtysh),
    )

    return f"{docker_compose_project_name}-frrouting-1"


@pytest.fixture
def vtysh(frr_container) -> Vtysh:
    """Return a Vtysh instance.

    The FRR container is implicitly started by requesting the frr_container fixture.
    """
    return Vtysh(container=frr_container)


@pytest.fixture
def bgp_prefix_configured() -> Callable[[_IP_Prefix, Vtysh, VRF], bool]:
    """A callable that can be used to check if a BGP prefix is configured."""

    def _(prefix: _IP_Prefix, vtysh: Vtysh, vrf: VRF = None) -> bool:
        family = get_afi(prefix)
        cmd = (
            f"show ip bgp vrf {vrf} {family} unicast {prefix} json"
            if vrf
            else f"show ip bgp {family} unicast {prefix} json"
        )
        show_prefix = vtysh(cmd, configure_terminal=False, context=[]).stdout
        prefix_info = json.loads(show_prefix)

        with suppress(KeyError):
            paths = prefix_info["paths"]
            origin = paths[0]["origin"]
            local = paths[0]["local"]
            if origin == "IGP" and local is True:
                return True

        return False

    return _


@pytest.fixture
def add_bgp_prefix() -> (
    Callable[[_IP_Prefix, int, Vtysh, VRF], subprocess.CompletedProcess]
):
    """A callable that can be used to add a BGP prefix."""

    def _(
        prefix: _IP_Prefix, asn: int, vtysh: Vtysh, vrf: VRF = None, **kwargs
    ) -> subprocess.CompletedProcess:
        """Add a network to the BGP configuration using vtysh."""
        family = get_afi(prefix)
        return vtysh(
            f"network {prefix}",
            configure_terminal=True,
            context=[
                f"router bgp {asn} vrf {vrf}" if vrf else f"router bgp {asn}",
                f"address-family {family} unicast",
            ],
            **kwargs,
        )

    return _


@pytest.fixture
def remove_bgp_prefix() -> (
    Callable[[_IP_Prefix, int, Vtysh, VRF], subprocess.CompletedProcess]
):
    """A callable that can be used to remove a BGP prefix."""

    def _(
        prefix: _IP_Prefix, asn: int, vtysh: Vtysh, vrf: VRF = None, **kwargs
    ) -> subprocess.CompletedProcess:
        """Remove a network from the BGP configuration using vtysh."""
        family = get_afi(prefix)
        return vtysh(
            f"no network {prefix}",
            configure_terminal=True,
            context=[
                f"router bgp {asn} vrf {vrf}" if vrf else f"router bgp {asn}",
                f"address-family {family} unicast",
            ],
            **kwargs,
        )

    return _
