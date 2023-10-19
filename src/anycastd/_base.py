import asyncio
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any


class BaseExecutor(ABC):
    """An interface to execute programs."""

    @abstractmethod
    async def create_subprocess_exec(  # noqa: PLR0913
        self,
        exec: str | Path,
        args: Sequence[str],
        *,
        stdout: Any = subprocess.PIPE,
        stderr: Any = subprocess.PIPE,
        text: bool = True,
    ) -> asyncio.subprocess.Process:
        """Create an async subprocess.

        Args:
            exec: The path of the program to execute.
            args: The arguments to pass to the program.
            stdout: The stdout file handle as specified in subprocess.Popen.
            stderr: The stderr file handle as specified in subprocess.Popen.
            text: Whether to decode the output as text.

        Returns:
            An asyncio.subprocess.Process object.
        """
        raise NotImplementedError
