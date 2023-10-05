import asyncio
import ipaddress
import json
import subprocess
from contextlib import suppress

from anycastd.prefix.base import BasePrefix

VTYSH_BIN = "/usr/bin/vtysh"


class FRRoutingPrefix(BasePrefix):
    async def is_announced(self) -> bool:
        """Returns True if the prefix is announced.

        Checks if the respective BGP prefix is configured in the default VRF.
        """
        family = get_afi(self)
        show_prefix = await _run_vtysh_commands(
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
        asn = await _get_default_local_asn()

        await _run_vtysh_commands(
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
        asn = await _get_default_local_asn()

        await _run_vtysh_commands(
            (
                "configure terminal",
                f"router bgp {asn}",
                f"address-family {family} unicast",
                f"no network {self.prefix}",
            )
        )


def get_afi(prefix: BasePrefix) -> str:
    """Return the FRR string AFI for the given IP type."""
    return "ipv6" if not isinstance(prefix.prefix, ipaddress.IPv4Network) else "ipv4"


async def _get_default_local_asn() -> int:
    """Returns the local ASN in the default VRF.

    Raises:
        RuntimeError: Failed to get the local ASN.
    """
    show_bgp_detail = await _run_vtysh_commands(("show bgp detail json",))
    bgp_detail = json.loads(show_bgp_detail)

    if warning := bgp_detail.get("warning"):
        raise RuntimeError(f"Failed to get local ASN: {warning}")

    return int(bgp_detail["localAS"])


async def _run_vtysh_commands(commands: tuple[str, ...]) -> str:
    """Run commands in the vtysh.

    Raises:
        RuntimeError: The command exited with a non-zero exit code.
    """
    proc = await asyncio.create_subprocess_exec(
        VTYSH_BIN, "-c", *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
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
