"""Inbound generators for sing-box exporter."""

from typing import Any

from sboxmgr.subscription.models import ClientProfile


def generate_inbounds(profile: ClientProfile) -> list[dict[str, Any]]:
    """Generate inbounds section for sing-box config based on ClientProfile.

    Args:
        profile: Client profile with inbound descriptions.

    Returns:
        List of inbounds for sing-box configuration.

    Security Notes:
        - Binds to localhost (127.0.0.1) by default.
        - Safe default ports, external bind only with explicit confirmation.
        - Validation through pydantic.
    """
    inbounds = []

    for inbound in profile.inbounds:
        # Create base inbound structure
        inb = {"type": inbound.type, "tag": _get_inbound_tag(inbound)}

        # Special handling for tun
        if inbound.type == "tun":
            _configure_tun_inbound(inb, inbound)
        else:
            _configure_regular_inbound(inb, inbound)

        # Remove None fields for compactness
        inb = {k: v for k, v in inb.items() if v is not None}
        inbounds.append(inb)

    return inbounds


def _get_inbound_tag(inbound) -> str:
    """Get inbound tag from options or generate default.

    Args:
        inbound: Inbound configuration object.

    Returns:
        Inbound tag string.
    """
    if inbound.options and inbound.options.get("tag"):
        return inbound.options["tag"]
    return f"{inbound.type}-in"


def _configure_tun_inbound(inb: dict[str, Any], inbound) -> None:
    """Configure TUN inbound with special handling.

    Args:
        inb: Inbound configuration to modify.
        inbound: Source inbound object.
    """
    # Add all fields from options to root for TUN
    if inbound.options:
        for key, value in inbound.options.items():
            if key != "tag":  # tag already added
                inb[key] = value


def _configure_regular_inbound(inb: dict[str, Any], inbound) -> None:
    """Configure regular (non-TUN) inbound.

    Args:
        inb: Inbound configuration to modify.
        inbound: Source inbound object.
    """
    # Add listen and port fields
    if hasattr(inbound, "listen") and inbound.listen:
        inb["listen"] = inbound.listen
    if hasattr(inbound, "port") and inbound.port:
        inb["listen_port"] = inbound.port

    # Add other fields from options
    if inbound.options:
        for key, value in inbound.options.items():
            if key not in ["tag", "listen", "port"]:  # These fields already processed
                inb[key] = value
