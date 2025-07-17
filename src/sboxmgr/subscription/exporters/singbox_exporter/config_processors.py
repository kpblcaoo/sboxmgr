"""Configuration processors for sing-box exporter."""

import logging
from typing import Any, Optional

from sboxmgr.subscription.models import ParsedServer

from .constants import CONFIG_WHITELIST, PROTOCOL_NORMALIZATION, TLS_CONFIG_FIELDS

logger = logging.getLogger(__name__)


def create_base_outbound(server: ParsedServer, protocol_type: str) -> dict[str, Any]:
    """Create base outbound structure.

    Args:
        server: ParsedServer object.
        protocol_type: Normalized protocol type.

    Returns:
        Base outbound configuration dictionary.
    """
    return {
        "type": protocol_type,
        "server": server.address,
        "server_port": server.port,
    }


def normalize_protocol_type(server_type: str) -> str:
    """Normalize protocol type for sing-box.

    Args:
        server_type: Original protocol type.

    Returns:
        Normalized protocol type.
    """
    return PROTOCOL_NORMALIZATION.get(server_type, server_type)


def process_shadowsocks_config(
    outbound: dict[str, Any], server: ParsedServer, meta: dict[str, Any]
) -> bool:
    """Process Shadowsocks configuration.

    Args:
        outbound: Outbound configuration to modify.
        server: Source server.
        meta: Server metadata.

    Returns:
        True if configuration is valid, False if server should be skipped.
    """
    method = meta.get("cipher") or meta.get("method") or server.security
    if not method:
        logger.warning(
            f"WARNING: shadowsocks outbound without method/cipher, skipping: {server.address}:{server.port}"
        )
        return False

    # Add required fields
    outbound["method"] = method

    # Add password - required field for shadowsocks
    password = server.password or meta.get("password")
    if not password:
        logger.warning(
            f"WARNING: shadowsocks outbound without password, skipping: {server.address}:{server.port}"
        )
        return False
    outbound["password"] = password

    return True


def process_transport_config(outbound: dict[str, Any], meta: dict[str, Any]) -> None:
    """Process transport configuration (ws, grpc, tcp, udp).

    Args:
        outbound: Outbound configuration to modify.
        meta: Server metadata to modify.
    """
    network = meta.pop("network", None)
    if network in ("ws", "grpc"):
        outbound["transport"] = {"type": network}
        # Move network-specific fields to transport
        for key in list(meta.keys()):
            if key.startswith(network):
                transport_key = key[len(network) + 1 :]
                outbound["transport"][transport_key] = meta.pop(key)
    elif network in ("tcp", "udp"):
        outbound["network"] = network


def process_tls_config(
    outbound: dict[str, Any], meta: dict[str, Any], protocol_type: str
) -> None:
    """Process TLS configuration.

    Args:
        outbound: Outbound configuration to modify.
        meta: Server metadata to modify.
        protocol_type: Protocol type for TLS handling.
    """
    if protocol_type in ("vless", "vmess", "trojan"):
        # These protocols handle TLS at transport level
        if meta.get("security") == "tls":
            outbound["tls"] = {"enabled": True}

            # Process TLS-specific fields
            for field in TLS_CONFIG_FIELDS:
                if field in meta and field != "tls":
                    if "tls" not in outbound:
                        outbound["tls"] = {}
                    outbound["tls"][field] = meta.pop(field)
        elif meta.get("security") == "reality":
            outbound["tls"] = {"enabled": True, "reality": True}
            # Process reality-specific fields
            for key in ["public_key", "short_id", "spx"]:
                if key in meta:
                    outbound["tls"][key] = meta.pop(key)

    # Remove processed security field
    meta.pop("security", None)


def process_auth_and_flow_config(
    outbound: dict[str, Any], meta: dict[str, Any]
) -> None:
    """Process authentication and flow configuration.

    Args:
        outbound: Outbound configuration to modify.
        meta: Server metadata to modify.
    """
    # UUID for authentication
    if meta.get("uuid"):
        outbound["uuid"] = meta.pop("uuid")

    # Flow control
    if meta.get("flow"):
        outbound["flow"] = meta.pop("flow")


def process_tag_config(
    outbound: dict[str, Any], server: ParsedServer, meta: dict[str, Any]
) -> None:
    """Process tag configuration.

    Args:
        outbound: Outbound configuration to modify.
        server: Source server.
        meta: Server metadata.
    """
    # Priority: server.tag (normalized by middleware) > meta['name'] > generated tag
    if hasattr(server, "tag") and server.tag:
        outbound["tag"] = server.tag
    elif meta.get("name"):
        outbound["tag"] = meta["name"]
    else:
        outbound["tag"] = f"{outbound['type']}-{server.address}"


def process_additional_config(outbound: dict[str, Any], meta: dict[str, Any]) -> None:
    """Process additional configuration parameters.

    Args:
        outbound: Outbound configuration to modify.
        meta: Server metadata.
    """
    # Only include whitelisted fields
    for key, value in meta.items():
        if key in CONFIG_WHITELIST:
            outbound[key] = value


def process_standard_server(
    server: ParsedServer, protocol_type: str
) -> Optional[dict[str, Any]]:
    """Process standard server (non-special protocol).

    Args:
        server: ParsedServer to process.
        protocol_type: Normalized protocol type.

    Returns:
        Outbound configuration or None if server should be skipped.
    """
    outbound = create_base_outbound(server, protocol_type)
    meta = dict(server.meta or {})

    # Process Shadowsocks configuration
    if protocol_type == "shadowsocks":
        if not process_shadowsocks_config(outbound, server, meta):
            return None

    # Process various configuration aspects
    process_transport_config(outbound, meta)
    process_tls_config(outbound, meta, protocol_type)
    process_auth_and_flow_config(outbound, meta)
    process_tag_config(outbound, server, meta)
    process_additional_config(outbound, meta)

    return outbound
