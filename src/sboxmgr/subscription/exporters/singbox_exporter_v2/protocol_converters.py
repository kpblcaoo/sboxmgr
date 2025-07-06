"""Protocol-specific converters for sing-box exporter v2.

This module provides conversion functions for each supported protocol type,
transforming ParsedServer objects into appropriate sing-box outbound models.
"""

import logging
from typing import Any, Dict, Optional

# Import new sing-box models
from sboxmgr.models.singbox import (
    AnyTlsOutbound,
    DirectOutbound,
    HttpOutbound,
    Hysteria2Outbound,
    ShadowsocksOutbound,
    ShadowTlsOutbound,
    SocksOutbound,
    SshOutbound,
    TorOutbound,
    TrojanOutbound,
    TuicOutbound,
    VlessOutbound,
    VmessOutbound,
    WireGuardOutbound,
)

from ...models import ParsedServer
from .utils import convert_tls_config, convert_transport_config

logger = logging.getLogger(__name__)


def convert_shadowsocks(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[ShadowsocksOutbound]:
    """Convert ParsedServer to ShadowsocksOutbound."""
    method = server.meta.get("cipher") or server.meta.get("method") or server.security
    if not method:
        logger.warning(
            f"Shadowsocks server without method: {server.address}:{server.port}"
        )
        return None

    outbound_data = {
        **base_data,
        "method": method,
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("plugin"):
        outbound_data["plugin"] = server.meta["plugin"]
    if server.meta.get("plugin_opts"):
        outbound_data["plugin_opts"] = server.meta["plugin_opts"]
    if server.meta.get("udp_over_tcp"):
        outbound_data["udp_over_tcp"] = server.meta["udp_over_tcp"]

    return ShadowsocksOutbound(**outbound_data)


def convert_vmess(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[VmessOutbound]:
    """Convert ParsedServer to VmessOutbound."""
    outbound_data = {
        **base_data,
        "uuid": server.uuid or server.meta.get("uuid"),
    }

    # Add security only if it's a valid value
    valid_security = {"auto", "aes-128-gcm", "chacha20-poly1305", "none"}
    sec = server.meta.get("security")
    if sec in valid_security:
        outbound_data["security"] = sec

    # Add optional fields
    if server.meta.get("alter_id"):
        outbound_data["alter_id"] = server.meta["alter_id"]
    if server.meta.get("global_padding"):
        outbound_data["global_padding"] = server.meta["global_padding"]
    if server.meta.get("authenticated_length"):
        outbound_data["authenticated_length"] = server.meta["authenticated_length"]
    if server.meta.get("packet_encoding"):
        outbound_data["packet_encoding"] = server.meta["packet_encoding"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        transport_config = convert_transport_config(server)
        if transport_config:
            outbound_data["transport"] = transport_config

    return VmessOutbound(**outbound_data)


def convert_vless(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[VlessOutbound]:
    """Convert ParsedServer to VlessOutbound."""
    outbound_data = {
        **base_data,
        "uuid": server.uuid or server.meta.get("uuid"),
        "flow": server.meta.get("flow"),
    }

    # Add optional fields
    if server.meta.get("packet_encoding"):
        outbound_data["packet_encoding"] = server.meta["packet_encoding"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        transport_config = convert_transport_config(server)
        if transport_config:
            outbound_data["transport"] = transport_config

    return VlessOutbound(**outbound_data)


def convert_trojan(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[TrojanOutbound]:
    """Convert ParsedServer to TrojanOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("fallback"):
        outbound_data["fallback"] = server.meta["fallback"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        transport_config = convert_transport_config(server)
        if transport_config:
            outbound_data["transport"] = transport_config

    return TrojanOutbound(**outbound_data)


def convert_hysteria2(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[Hysteria2Outbound]:
    """Convert ParsedServer to Hysteria2Outbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("up_mbps"):
        outbound_data["up_mbps"] = server.meta["up_mbps"]
    if server.meta.get("down_mbps"):
        outbound_data["down_mbps"] = server.meta["down_mbps"]
    if server.meta.get("obfs"):
        outbound_data["obfs"] = server.meta["obfs"]
    if server.meta.get("obfs_type"):
        outbound_data["obfs_type"] = server.meta["obfs_type"]
    if server.meta.get("obfs_password"):
        outbound_data["obfs_password"] = server.meta["obfs_password"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    return Hysteria2Outbound(**outbound_data)


def convert_wireguard(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[WireGuardOutbound]:
    """Convert ParsedServer to WireGuardOutbound."""
    outbound_data = {
        **base_data,
        "private_key": server.private_key or server.meta.get("private_key"),
        "peer_public_key": getattr(server, "peer_public_key", None)
        or getattr(server, "public_key", None)
        or server.meta.get("peer_public_key")
        or server.meta.get("public_key"),
    }

    # Add optional fields
    if getattr(server, "local_address", None) or server.meta.get("local_address"):
        outbound_data["local_address"] = getattr(
            server, "local_address", None
        ) or server.meta.get("local_address")
    if getattr(server, "pre_shared_key", None) or server.meta.get("pre_shared_key"):
        outbound_data["pre_shared_key"] = getattr(
            server, "pre_shared_key", None
        ) or server.meta.get("pre_shared_key")
    if server.meta.get("reserved"):
        outbound_data["reserved"] = server.meta["reserved"]
    if server.meta.get("mtu"):
        outbound_data["mtu"] = server.meta["mtu"]
    if server.meta.get("keepalive"):
        outbound_data["keepalive"] = server.meta["keepalive"]
    if server.meta.get("workers"):
        outbound_data["workers"] = server.meta["workers"]

    return WireGuardOutbound(**outbound_data)


def convert_tuic(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[TuicOutbound]:
    """Convert ParsedServer to TuicOutbound."""
    outbound_data = {
        **base_data,
        "uuid": server.uuid or server.meta.get("uuid"),
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("congestion_control"):
        outbound_data["congestion_control"] = server.meta["congestion_control"]
    if server.meta.get("udp_relay_mode"):
        outbound_data["udp_relay_mode"] = server.meta["udp_relay_mode"]
    if server.meta.get("zero_rtt_handshake"):
        outbound_data["zero_rtt_handshake"] = server.meta["zero_rtt_handshake"]
    if server.meta.get("heartbeat"):
        outbound_data["heartbeat"] = server.meta["heartbeat"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    return TuicOutbound(**outbound_data)


def convert_shadowtls(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[ShadowTlsOutbound]:
    """Convert ParsedServer to ShadowTlsOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("version"):
        outbound_data["version"] = server.meta["version"]
    if server.meta.get("handshake"):
        outbound_data["handshake"] = server.meta["handshake"]
    if server.meta.get("handshake_for_server_name"):
        outbound_data["handshake_for_server_name"] = server.meta[
            "handshake_for_server_name"
        ]
    if server.meta.get("strict_mode"):
        outbound_data["strict_mode"] = server.meta["strict_mode"]

    # Add TLS if present
    if (
        server.tls
        or server.meta.get("tls")
        or server.meta.get("servername")
        or server.meta.get("alpn")
    ):
        tls_config = convert_tls_config(server)
        if tls_config:
            outbound_data["tls"] = tls_config

    return ShadowTlsOutbound(**outbound_data)


def convert_anytls(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[AnyTlsOutbound]:
    """Convert ParsedServer to AnyTlsOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password"),
    }

    # Add optional fields
    if server.meta.get("idle_session_check_interval"):
        outbound_data["idle_session_check_interval"] = server.meta[
            "idle_session_check_interval"
        ]
    if server.meta.get("idle_session_timeout"):
        outbound_data["idle_session_timeout"] = server.meta["idle_session_timeout"]
    if server.meta.get("min_idle_session"):
        outbound_data["min_idle_session"] = server.meta["min_idle_session"]

    return AnyTlsOutbound(**outbound_data)


def convert_tor(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[TorOutbound]:
    """Convert ParsedServer to TorOutbound."""
    outbound_data = base_data.copy()

    # Add optional fields
    if server.meta.get("executable_path"):
        outbound_data["executable_path"] = server.meta["executable_path"]
    if server.meta.get("extra_args"):
        outbound_data["extra_args"] = server.meta["extra_args"]
    if server.meta.get("data_directory"):
        outbound_data["data_directory"] = server.meta["data_directory"]
    if server.meta.get("torrc"):
        outbound_data["torrc"] = server.meta["torrc"]

    return TorOutbound(**outbound_data)


def convert_ssh(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[SshOutbound]:
    """Convert ParsedServer to SshOutbound."""
    outbound_data = {**base_data, "user": server.username or server.meta.get("user")}

    # Add optional fields
    if server.password or server.meta.get("password"):
        outbound_data["password"] = server.password or server.meta.get("password")
    if server.private_key or server.meta.get("private_key"):
        outbound_data["private_key"] = server.private_key or server.meta.get(
            "private_key"
        )
    if server.meta.get("private_key_path"):
        outbound_data["private_key_path"] = server.meta["private_key_path"]
    if server.meta.get("private_key_passphrase"):
        outbound_data["private_key_passphrase"] = server.meta["private_key_passphrase"]
    if server.meta.get("host_key"):
        outbound_data["host_key"] = server.meta["host_key"]
    if server.meta.get("host_key_algorithms"):
        outbound_data["host_key_algorithms"] = server.meta["host_key_algorithms"]
    if server.meta.get("client_version"):
        outbound_data["client_version"] = server.meta["client_version"]

    return SshOutbound(**outbound_data)


def convert_http(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[HttpOutbound]:
    """Convert ParsedServer to HttpOutbound."""
    outbound_data = base_data.copy()

    # Add optional fields
    if server.username or server.meta.get("username"):
        outbound_data["username"] = server.username or server.meta.get("username")
    if server.password or server.meta.get("password"):
        outbound_data["password"] = server.password or server.meta.get("password")
    if server.meta.get("path"):
        outbound_data["path"] = server.meta["path"]

    return HttpOutbound(**outbound_data)


def convert_socks(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[SocksOutbound]:
    """Convert ParsedServer to SocksOutbound."""
    outbound_data = base_data.copy()

    # Add optional fields
    if server.username or server.meta.get("username"):
        outbound_data["username"] = server.username or server.meta.get("username")
    if server.password or server.meta.get("password"):
        outbound_data["password"] = server.password or server.meta.get("password")
    if server.meta.get("version"):
        outbound_data["version"] = server.meta["version"]

    return SocksOutbound(**outbound_data)


def convert_direct(
    server: ParsedServer, base_data: Dict[str, Any]
) -> Optional[DirectOutbound]:
    """Convert ParsedServer to DirectOutbound."""
    outbound_data = base_data.copy()

    # Add optional fields
    if server.meta.get("override_address"):
        outbound_data["override_address"] = server.meta["override_address"]
    if server.meta.get("override_port"):
        outbound_data["override_port"] = server.meta["override_port"]
    if server.meta.get("proxy"):
        outbound_data["proxy"] = server.meta["proxy"]

    return DirectOutbound(**outbound_data)
