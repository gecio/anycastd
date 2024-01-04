import asyncio
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any


class Executor(ABC):
    """An interface to execute programs."""

    @abstractmethod
    async def create_subprocess_exec(
        self,
        exec: str | Path,
        args: Sequence[str],
        *,
        stdout: int | IO[Any] | None = subprocess.PIPE,
        stderr: int | IO[Any] | None = subprocess.PIPE,
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess.

        Args:
            exec: The path of the program to execute.
            args: The arguments to pass to the program.
            stdout: The stdout file handle as specified in subprocess.Popen.
            stderr: The stderr file handle as specified in subprocess.Popen.

        Returns:
            An asyncio.subprocess.Process object.
        """
        raise NotImplementedError


@dataclass
class LocalExecutor(Executor):
    """An executor that runs commands locally."""

    async def create_subprocess_exec(
        self,
        exec: str | Path,
        args: Sequence[str],
        *,
        stdout: int | IO[Any] | None = subprocess.PIPE,
        stderr: int | IO[Any] | None = subprocess.PIPE,
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess.

        This method simply wraps asyncio.create_subprocess_exec.

        Args:
            exec: The path of the program to execute.
            args: The arguments to pass to the program.
            stdout: The stdout file handle as specified in subprocess.Popen.
            stderr: The stderr file handle as specified in subprocess.Popen.

        Returns:
            An asyncio.subprocess.Process object.
        """
        return await asyncio.create_subprocess_exec(
            exec, *args, stdout=stdout, stderr=stderr
        )


@dataclass
class DockerExecutor(Executor):
    """An executor that runs commands in a Docker container.

    Attributes:
        docker: The path to the Docker executable.
        container: The name of the container to run commands in.
    """

    docker: Path
    container: str

    async def create_subprocess_exec(
        self,
        exec: str | Path,
        args: Sequence[str],
        *,
        stdout: int | IO[Any] | None = subprocess.PIPE,
        stderr: int | IO[Any] | None = subprocess.PIPE,
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess inside of a Docker container.

        Wraps the interface of asyncio.create_subprocess_exec while running
        the command inside of a Docker container.

        Args:
            exec: The path of the program to execute.
            args: The arguments to pass to the program.
            stdout: The stdout file handle as specified in subprocess.Popen.
            stderr: The stderr file handle as specified in subprocess.Popen.

        Returns:
            An asyncio.subprocess.Process object.
        """
        docker_args = ("exec", "-i", self.container, exec, *args)
        return await asyncio.create_subprocess_exec(
            self.docker, *docker_args, stdout=stdout, stderr=stderr
        )
