import json
import subprocess
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from typing import TypeAlias

import pytest

_Prefix: TypeAlias = IPv4Network | IPv6Network


def get_afi(prefix: _Prefix) -> str:
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
    ) -> str:
        """Run a command and return the output.

        Arguments:
            command: The command to run.
            configure_terminal: Run the command in a configure terminal.
            context: Run the command in a specific context.

        Returns:
            The output of the command.
        """
        configure_terminal = configure_terminal or self.configure_terminal
        context = context or self.context

        vty_cmd = []
        if configure_terminal:
            vty_cmd.append("configure terminal")
        if context:
            vty_cmd.extend(self.context)
        vty_cmd.append(command)

        docker_cmd = ["exec", "-i", self.container, "vtysh", "-c", "\n".join(vty_cmd)]

        result = subprocess.run(
            [self.docker.as_posix(), *docker_cmd],
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            msg = f"Failed to run command in {self}:\n"
            if result.stdout:
                msg += f"stdout: {result.stdout}\n"
            if result.stderr:
                msg += f"stderr: {result.stderr}\n"
            raise RuntimeError(msg)

        return result.stdout

    def exit(self, *, all: bool = False) -> None:
        """Exit the current context.

        Arguments:
            all: Exit all contexts.
        """
        if all:
            self.context.clear()
        else:
            self.context.pop()


@pytest.fixture
def vtysh(docker_services, docker_compose_project_name) -> Vtysh:
    """Return a Vtysh instance."""
    container = f"{docker_compose_project_name}-frrouting-1"
    return Vtysh(container=container)


@pytest.fixture
def bgp_prefix_configured() -> Callable[[_Prefix, Vtysh], bool]:
    """A callable that can be used to check if a BGP prefix is configured."""

    def _(prefix: _Prefix, vtysh: Vtysh) -> bool:
        family = get_afi(prefix)
        show_prefix = vtysh(
            f"show ip bgp {family} unicast {prefix} json",
            configure_terminal=False,
            context=[],
        )
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
def add_bgp_prefix() -> Callable[[_Prefix, int, Vtysh], None]:
    """A callable that can be used to add a BGP prefix."""

    def _(prefix: _Prefix, asn: int, vtysh: Vtysh) -> None:
        """Add a network to the BGP configuration using vtysh."""
        family = get_afi(prefix)
        vtysh(
            f"network {prefix}",
            configure_terminal=True,
            context=[f"router bgp {asn}", f"address-family {family} unicast"],
        )

    return _
