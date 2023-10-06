import asyncio
import json
import subprocess
from contextlib import suppress
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path

from anycastd.prefix.base import BasePrefix


class FRRoutingPrefix(BasePrefix):
    vtysh: Path

    def __init__(
        self, prefix: IPv4Network | IPv6Network, *, vtysh: Path = Path("/usr/bin/vtysh")
    ):
        super().__init__(prefix)
        self.vtysh = vtysh

    async def is_announced(self) -> bool:
        """Returns True if the prefix is announced.

        Checks if the respective BGP prefix is configured in the default VRF.
        """
        family = get_afi(self)
        show_prefix = await self._run_vtysh_commands(
            (f"show bgp {family} unicast {self.prefix} json",)
        )
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
        asn = await self._get_default_local_asn()

        await self._run_vtysh_commands(
            (
                "configure terminal",
                f"router bgp {asn}",
                f"address-family {family} unicast",
                f"network {self.prefix}",
            )
        )

    async def denounce(self) -> None:
        """Denounce the prefix in the default VRF.

        Removes the respective BGP prefix from the default VRF.
        """
        family = get_afi(self)
        asn = await self._get_default_local_asn()

        await self._run_vtysh_commands(
            (
                "configure terminal",
                f"router bgp {asn}",
                f"address-family {family} unicast",
                f"no network {self.prefix}",
            )
        )

    async def _get_default_local_asn(self) -> int:
        """Returns the local ASN in the default VRF.

        Raises:
            RuntimeError: Failed to get the local ASN.
        """
        show_bgp_detail = await self._run_vtysh_commands(("show bgp detail json",))
        bgp_detail = json.loads(show_bgp_detail)
        if warning := bgp_detail.get("warning"):
            raise RuntimeError(f"Failed to get local ASN: {warning}")
        return int(bgp_detail["localAS"])

    async def _run_vtysh_commands(self, commands: tuple[str, ...]) -> str:
        """Run commands in the vtysh.

        Raises:
            RuntimeError: The command exited with a non-zero exit code.
        """
        vty_cmd = "\n".join(commands)
        proc = await asyncio.create_subprocess_exec(
            self.vtysh, "-c", vty_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
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
