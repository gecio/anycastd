import json
from collections.abc import Sequence
from contextlib import suppress
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from typing import TypeAlias

from anycastd._base import BaseExecutor
from anycastd.prefix.base import BasePrefix

VRF: TypeAlias = str | None


class FRRoutingPrefix(BasePrefix):
    vrf: VRF
    vtysh: Path
    executor: BaseExecutor

    def __init__(
        self,
        prefix: IPv4Network | IPv6Network,
        *,
        vrf: VRF = None,
        vtysh: Path = Path("/usr/bin/vtysh"),
        executor: BaseExecutor,
    ):
        super().__init__(prefix)
        self.vrf = vrf
        self.vtysh = vtysh
        self.executor = executor

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
            RuntimeError: The command exited with a non-zero exit code.
        """
        proc = await self.executor.create_subprocess_exec(
            self.vtysh, ("-c", "\n".join(commands))
        )
        stdout, stderr = await proc.communicate()

        # Command may have failed even if the returncode is 0.
        if proc.returncode != 0 or stderr:
            msg = f"Failed to run vtysh commands {', '.join(commands)}:\n"
            if stdout:
                msg += "stdout: {}\n".format(stdout.decode("utf-8"))
            if stderr:
                msg += "stderr: {}\n".format(stderr.decode("utf-8"))
            raise RuntimeError(msg)

        return stdout.decode("utf-8")


def get_afi(prefix: BasePrefix) -> str:
    """Return the FRR string AFI for the given IP type."""
    return "ipv6" if not isinstance(prefix.prefix, IPv4Network) else "ipv4"
