import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from ipaddress import IPv4Network
from pathlib import Path

import pytest
import stamina
from anycastd.prefix import VRF
from testcontainers.core.container import DockerContainer

from tests.conftest import _IP_Prefix

FRR_DOCKER_IMAGE = "quay.io/frrouting/frr:{}".format(
    os.environ.get("FRR_VERSION", "master")
)


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


def wait_for_frr_daemons(vtysh) -> None:
    """Wait for all FRR daemons to be up.

    Parses the output of `show watchfrr` and returns once all daemons are up.
    If the daemons are not up after 60 seconds, an AssertionError is raised.

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
    for attempt in stamina.retry_context(
        on=AssertionError, wait_max=0.1, attempts=None, timeout=60
    ):
        with attempt:
            watchfrr_status = vtysh("show watchfrr").stdout
            assert all(
                "Up" in daemon[1]
                for daemon in re_daemon_status.findall(watchfrr_status)
            )


@pytest.fixture(scope="module")
def frr_container_name() -> str:
    return "frrouting-integration-tests"


@pytest.fixture(scope="module")
def frr_container_vtysh(frr_container_name):
    """Create a FRRouting container and return a Vtysh instance to it.

    Spins up a FRRouting container with basic configuration, waits for all FRR daemons
    to be up and returns a Vtysh instance configured to run commands in the container.
    """
    files_dir = Path(__file__).parent / "files"
    container = DockerContainer(FRR_DOCKER_IMAGE, privileged=True)
    container.with_name(frr_container_name)
    container.with_exposed_ports(2616, 2616)
    container.with_volume_mapping(
        (files_dir / "daemons").as_posix(), "/etc/frr/daemons", "ro"
    )
    container.with_volume_mapping(
        (files_dir / "vtysh.conf").as_posix(), "/etc/frr/vtysh.conf", "ro"
    )
    container.with_volume_mapping(
        (files_dir / "frr.conf").as_posix(), "/etc/frr/frr.conf", "ro"
    )

    with container:
        vtysh = Vtysh(container=frr_container_name)
        wait_for_frr_daemons(vtysh)
        yield vtysh


@pytest.fixture
def frr_container_reset_bgp_config(frr_container_vtysh):
    """Reset the BGP configuration."""
    asn = 65536

    re_bgp_configs = re.compile(r"^router bgp .*$", re.MULTILINE)
    for bgp_config in re_bgp_configs.findall(frr_container_vtysh("sh run").stdout):
        frr_container_vtysh(f"no {bgp_config}", configure_terminal=True)

    frr_container_vtysh(
        "bgp router-id 1.3.3.7", configure_terminal=True, context=[f"router bgp {asn}"]
    )


@pytest.fixture
def bgp_prefix_configured() -> Callable[[_IP_Prefix, Vtysh, VRF], bool]:
    """A callable that can be used to check if a BGP prefix is configured."""

    def _(prefix: _IP_Prefix, vtysh: Vtysh, vrf: VRF = None) -> bool:
        running_config = vtysh("show running-config").stdout
        return (
            re.search(rf"^  network {prefix}$", running_config, re.MULTILINE)
            is not None
        )

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
