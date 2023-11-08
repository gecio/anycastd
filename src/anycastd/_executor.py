import asyncio
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from anycastd._base import BaseExecutor


class LocalExecutor(BaseExecutor):
    """An executor that runs commands locally."""

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

        This method simply wraps asyncio.create_subprocess_exec.

        Args:
            exec: The path of the program to execute.
            args: The arguments to pass to the program.
            stdout: The stdout file handle as specified in subprocess.Popen.
            stderr: The stderr file handle as specified in subprocess.Popen.
            text: Whether to decode the output as text.

        Returns:
            An asyncio.subprocess.Process object.
        """
        return await asyncio.create_subprocess_exec(
            exec, *args, stdout=stdout, stderr=stderr, text=text
        )
