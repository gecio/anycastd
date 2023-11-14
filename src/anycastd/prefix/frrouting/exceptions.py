from collections.abc import Sequence


class FRRCommandError(Exception):
    """Failed to run a FRRouting VTY command."""

    commands: Sequence[str]
    exit_code: int
    stdout: str | None
    stderr: str | None

    def __init__(
        self,
        commands: Sequence[str],
        exit_code: int,
        stdout: str | None,
        stderr: str | None,
    ):
        self.commands = commands
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

        msg = f"Failed to run FRRouting VTY commands: {', '.join(self.commands)}:\n"
        if self.stdout:
            msg += f"stdout: {self.stdout}\n"
        if self.stderr:
            msg += f"stderr: {self.stderr}\n"
        super().__init__(msg)
