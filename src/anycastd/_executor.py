import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Executor(Protocol):
    """An interface to execute programs."""

    async def create_subprocess_exec(
        self, program: str | Path, *args: str
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess.

        Args:
            program: The path of the program to execute.
            args: The arguments to pass to the program.

        Returns:
            An asyncio.subprocess.Process object.
        """
        raise NotImplementedError


@dataclass
class LocalExecutor:
    """An executor that runs commands locally."""

    async def create_subprocess_exec(
        self, program: str | Path, *args: str
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess.

        This method simply wraps asyncio.create_subprocess_exec.

        Args:
            program: The path of the program to execute.
            args: The arguments to pass to the program.

        Returns:
            An asyncio.subprocess.Process object.
        """
        return await asyncio.create_subprocess_exec(
            program,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )


@dataclass
class DockerExecutor:
    """An executor that runs commands in a Docker container.

    Attributes:
        docker: The path to the Docker executable.
        container: The name of the container to run commands in.
    """

    docker: Path
    container: str

    async def create_subprocess_exec(
        self, program: str | Path, *args: str
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess inside of a Docker container.

        Wraps the interface of asyncio.create_subprocess_exec while running
        the command inside of a Docker container.

        Args:
            program: The path of the program to execute.
            args: The arguments to pass to the program.

        Returns:
            An asyncio.subprocess.Process object.
        """
        docker_args = ("exec", "-i", self.container, program, *args)
        return await asyncio.create_subprocess_exec(
            self.docker,
            *docker_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
