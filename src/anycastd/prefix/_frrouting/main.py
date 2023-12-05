import json
from collections.abc import Sequence
from contextlib import suppress
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from typing import Self, cast

from anycastd._executor import Executor
from anycastd.prefix._frrouting.exceptions import (
    FRRCommandError,
    FRRInvalidVRFError,
    FRRInvalidVTYSHError,
    FRRNoBGPError,
)
from anycastd.prefix._main import VRF, Prefix


class FRRoutingPrefix(Prefix):
    vrf: VRF
    vtysh: Path
    executor: Executor

    def __init__(
        self,
        prefix: IPv4Network | IPv6Network,
        *,
        vrf: VRF = None,
        vtysh: Path = Path("/usr/bin/vtysh"),
        executor: Executor,
    ) -> None:
        """Initialize the FRRouting prefix.

        It is recommended to use the `new` classmethod instead of this constructor
        to validate the prefix against the FRRouting configuration, avoiding
        potential errors later in runtime.
        """
        if not any((isinstance(prefix, IPv4Network), isinstance(prefix, IPv6Network))):
            raise TypeError("Prefix must be an IPv4 or IPv6 network.")
        self.__prefix = prefix
        self.vrf = vrf
        self.vtysh = vtysh
        self.executor = executor

    def __repr__(self) -> str:
        return (
            f"FRRoutingPrefix(prefix={self.prefix!r}, vrf={self.vrf!r}, "
            f"vtysh={self.vtysh!r}, executor={self.executor!r})"
        )

    @property
    def prefix(self) -> IPv4Network | IPv6Network:
        return self.__prefix

    async def is_announced(self) -> bool:
        """Returns True if the prefix is announced.

        Checks if the respective BGP prefix is configured in the default VRF.
        """
        family = get_afi(self)
        cmd = (
            f"show bgp vrf {self.vrf} {family} unicast {self.prefix} json"
            if self.vrf
            else f"show bgp {family} unicast {self.prefix} json"
        )
        show_prefix = await self._run_vtysh_commands((cmd,))
        prefix_info = json.loads(show_prefix)

        with suppress(KeyError):
            paths = prefix_info["paths"]
            origin = paths[0]["origin"]
            local = paths[0]["local"]
            if origin == "IGP" and local is True:
                return True

        return False

    async def announce(self) -> None:
        """Announce the prefix in the default VRF.

        Adds the respective BGP prefix to the default VRF.
        """
        family = get_afi(self)
        asn = await self._get_local_asn()

        await self._run_vtysh_commands(
            (
                "configure terminal",
                f"router bgp {asn} vrf {self.vrf}" if self.vrf else f"router bgp {asn}",
                f"address-family {family} unicast",
                f"network {self.prefix}",
            )
        )

    async def denounce(self) -> None:
        """Denounce the prefix in the default VRF.

        Removes the respective BGP prefix from the default VRF.
        """
        family = get_afi(self)
        asn = await self._get_local_asn()

        await self._run_vtysh_commands(
            (
                "configure terminal",
                f"router bgp {asn} vrf {self.vrf}" if self.vrf else f"router bgp {asn}",
                f"address-family {family} unicast",
                f"no network {self.prefix}",
            )
        )

    async def _get_local_asn(self) -> int:
        """Returns the local ASN in the VRF of the prefix.

        Raises:
            RuntimeError: Failed to get the local ASN.
        """
        show_bgp_detail = await self._run_vtysh_commands(
            (
                (
                    f"show bgp vrf {self.vrf} detail json"
                    if self.vrf
                    else "show bgp detail json"
                ),
            )
        )
        bgp_detail = json.loads(show_bgp_detail)
        if warning := bgp_detail.get("warning"):
            raise RuntimeError(f"Failed to get local ASN: {warning}")
        return int(bgp_detail["localAS"])

    async def _run_vtysh_commands(self, commands: Sequence[str]) -> str:
        """Run commands in the vtysh.

        Raises:
            FRRCommandFailed: The command failed to run due to a non-zero exit code
                or existing stderr output.
        """
        proc = await self.executor.create_subprocess_exec(
            self.vtysh, ("-c", "\n".join(commands))
        )
        stdout, stderr = await proc.communicate()

        # Command may have failed even if the returncode is 0.
        if proc.returncode != 0 or stderr:
            raise FRRCommandError(
                commands,
                cast(
                    int, proc.returncode
                ),  # Since we await the process above, this should never be None.
                stdout.decode("utf-8") if stdout else None,
                stderr.decode("utf-8") if stderr else None,
            )

        return stdout.decode("utf-8")

    async def validate(self) -> Self:
        """Validate the prefix, raising an error on invalid configuration.

        Checks if the required VRF and BGP configuration exists.

        Raises:
            FRRInvalidVTYSHError: The vtysh is invalid.
            FRRInvalidVRFError: The prefixes VRF is invalid and does not exist.
            FRRNoBGPError: BGP is not configured.
        """
        if not self.vtysh.is_file():
            raise FRRInvalidVTYSHError(self.vtysh, "The given VTYSH is not a file.")
        if self.vrf:
            show_vrf = await self._run_vtysh_commands((f"show bgp vrf {self.vrf}",))
            if "unknown" in show_vrf.lower():
                raise FRRInvalidVRFError(self.vrf)
        else:
            show_bgp = await self._run_vtysh_commands(("show bgp",))
            if "not found" in show_bgp.lower():
                raise FRRNoBGPError(self.vrf)

        return self

    @classmethod
    async def new(
        cls,
        prefix: IPv4Network | IPv6Network,
        *,
        vrf: VRF = None,
        vtysh: Path = Path("/usr/bin/vtysh"),
        executor: Executor,
    ) -> Self:
        """Create a new validated FRRoutingPrefix.

        Creates a new FRRoutingPrefix instance while validating it against the
        FRRouting configuration.

        Raises:
            A subclass of FRRConfigurationError if there is an issue with the
            FRRouting configuration.
        """
        return await cls(
            prefix=prefix, vrf=vrf, vtysh=vtysh, executor=executor
        ).validate()


def get_afi(prefix: Prefix) -> str:
    """Return the FRR string AFI for the given IP type."""
    return "ipv6" if not isinstance(prefix.prefix, IPv4Network) else "ipv4"
