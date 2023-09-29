import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest


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
                msg += f"stdout: {result.stdout}\n"
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
