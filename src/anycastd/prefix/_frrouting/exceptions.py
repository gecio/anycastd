from collections.abc import Sequence
from pathlib import Path

from anycastd.prefix._main import VRF


class FRRInvalidVTYSHError(Exception):
    """The FRRouting VTY shell is invalid."""

    vtysh: Path

    def __init__(self, vtysh: Path, reason: str):
        self.vtysh = vtysh
        super().__init__(f"The given VTYSH {self.vtysh} is invalid: {reason}.")


class FRRCommandError(Exception):
    """Failed to run a FRRouting VTY command."""

    commands: Sequence[str]
    exit_code: int | None
    stdout: str | None
    stderr: str | None

    def __init__(
        self,
        commands: Sequence[str],
        exit_code: int | None,
        *,
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


class FRRCommandTimeoutError(FRRCommandError):
    """The FRRouting VTY command timed out."""

    def __init__(self, commands: Sequence[str]):
        super().__init__(commands, None, stdout=None, stderr=None)


class FRRConfigurationError(Exception):
    """The FRR configuration is invalid."""


class FRRInvalidVRFError(FRRConfigurationError):
    """The VRF is not configured within FRR."""

    vrf: VRF

    def __init__(self, vrf: VRF):
        self.vrf = vrf
        super().__init__(f"The VRF {self.vrf} does not exist.")


class FRRNoBGPError(FRRConfigurationError):
    """BGP is not configured within FRR."""
