"""Compatibility layer for sing-box exporter v2.

This module provides backward compatibility for the original singbox_exporter_v2.py
while delegating all functionality to the new modular architecture.

The new modular structure is located in the singbox_exporter_v2/ package.
"""

import logging
import warnings

# Import all functionality from the new modular structure
from .singbox_exporter_v2 import (
    convert_parsed_server_to_outbound,
    convert_shadowsocks, convert_vmess, convert_vless, convert_trojan,
    convert_hysteria2, convert_wireguard, convert_tuic, convert_shadowtls,
    convert_anytls, convert_tor, convert_ssh, convert_http, convert_socks,
    convert_direct, convert_tls_config, convert_transport_config,
    convert_client_profile_to_inbounds, SingboxExporterV2
)

# Maintain backward compatibility with original imports
from .models import ParsedServer, ClientProfile
from .base_exporter import BaseExporter
from .registry import register

# Import new sing-box models for backward compatibility
from sboxmgr.models.singbox import (
    SingBoxConfig, LogConfig,
    # Inbounds
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound,
    # Outbounds
    ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
    Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
    TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
    BlockOutbound, SelectorOutbound, UrlTestOutbound, HysteriaOutbound,
    AnyTlsOutbound, SshOutbound, TorOutbound,
    # Common
    TlsConfig, TransportConfig, RouteConfig, RouteRule
)

logger = logging.getLogger(__name__)

# Issue deprecation warning for direct imports
warnings.warn(
    "Direct imports from singbox_exporter_v2.py are deprecated. "
    "Please use the modular singbox_exporter_v2 package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility aliases for protocol converter functions
_convert_shadowsocks = convert_shadowsocks
_convert_vmess = convert_vmess
_convert_vless = convert_vless
_convert_trojan = convert_trojan
_convert_hysteria2 = convert_hysteria2
_convert_wireguard = convert_wireguard
_convert_tuic = convert_tuic
_convert_shadowtls = convert_shadowtls
_convert_anytls = convert_anytls
_convert_tor = convert_tor
_convert_ssh = convert_ssh
_convert_http = convert_http
_convert_socks = convert_socks
_convert_direct = convert_direct

# Backward compatibility aliases for utility functions
_convert_tls_config = convert_tls_config
_convert_transport_config = convert_transport_config

# Re-export the main exporter class with registration
# (The registration is handled in the new modular structure)
__all__ = [
    'SingboxExporterV2',
    'convert_parsed_server_to_outbound',
    'convert_client_profile_to_inbounds',
    # Protocol converters
    'convert_shadowsocks', 'convert_vmess', 'convert_vless', 'convert_trojan',
    'convert_hysteria2', 'convert_wireguard', 'convert_tuic', 'convert_shadowtls',
    'convert_anytls', 'convert_tor', 'convert_ssh', 'convert_http', 'convert_socks',
    'convert_direct',
    # Utility functions
    'convert_tls_config', 'convert_transport_config',
    # Backward compatibility aliases
    '_convert_shadowsocks', '_convert_vmess', '_convert_vless', '_convert_trojan',
    '_convert_hysteria2', '_convert_wireguard', '_convert_tuic', '_convert_shadowtls',
    '_convert_anytls', '_convert_tor', '_convert_ssh', '_convert_http', '_convert_socks',
    '_convert_direct', '_convert_tls_config', '_convert_transport_config'
]


def convert_parsed_server_to_outbound(server: ParsedServer) -> Optional[Union[
    ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
    Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
    TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
    BlockOutbound, SelectorOutbound, UrlTestOutbound, HysteriaOutbound,
    AnyTlsOutbound, SshOutbound, TorOutbound
]]:
    """Convert ParsedServer to appropriate sing-box outbound model.

    Args:
        server: ParsedServer object to convert

    Returns:
        Appropriate outbound model instance or None if conversion fails

    """
    try:
        # Normalize protocol type
        protocol_type = server.type
        if protocol_type == "ss":
            protocol_type = "shadowsocks"

        # Create base outbound data
        outbound_data = {
            "type": protocol_type,
            "server": server.address,
            "server_port": server.port,
        }

        # Add tag
        if server.tag:
            outbound_data["tag"] = server.tag
        elif server.meta.get("name"):
            outbound_data["tag"] = server.meta["name"]
        else:
            outbound_data["tag"] = f"{protocol_type}-{server.address}"

        # Protocol-specific conversion
        if protocol_type == "shadowsocks":
            return _convert_shadowsocks(server, outbound_data)
        elif protocol_type == "vmess":
            return _convert_vmess(server, outbound_data)
        elif protocol_type == "vless":
            return _convert_vless(server, outbound_data)
        elif protocol_type == "trojan":
            return _convert_trojan(server, outbound_data)
        elif protocol_type == "hysteria2":
            return _convert_hysteria2(server, outbound_data)
        elif protocol_type == "wireguard":
            return _convert_wireguard(server, outbound_data)
        elif protocol_type == "tuic":
            return _convert_tuic(server, outbound_data)
        elif protocol_type == "shadowtls":
            return _convert_shadowtls(server, outbound_data)
        elif protocol_type == "anytls":
            return _convert_anytls(server, outbound_data)
        elif protocol_type == "tor":
            return _convert_tor(server, outbound_data)
        elif protocol_type == "ssh":
            return _convert_ssh(server, outbound_data)
        elif protocol_type == "http":
            return _convert_http(server, outbound_data)
        elif protocol_type == "socks":
            return _convert_socks(server, outbound_data)
        elif protocol_type == "direct":
            return _convert_direct(server, outbound_data)
        else:
            logger.warning(f"Unsupported protocol type: {protocol_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to convert server {server.address}:{server.port}: {e}")
        return None


def _convert_shadowsocks(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[ShadowsocksOutbound]:
    """Convert ParsedServer to ShadowsocksOutbound."""
    method = server.meta.get("cipher") or server.meta.get("method") or server.security
    if not method:
        logger.warning(f"Shadowsocks server without method: {server.address}:{server.port}")
        return None

    outbound_data = {
        **base_data,
        "method": method,
        "password": server.password or server.meta.get("password")
    }

    # Add optional fields
    if server.meta.get("plugin"):
        outbound_data["plugin"] = server.meta["plugin"]
    if server.meta.get("plugin_opts"):
        outbound_data["plugin_opts"] = server.meta["plugin_opts"]
    if server.meta.get("udp_over_tcp"):
        outbound_data["udp_over_tcp"] = server.meta["udp_over_tcp"]

    return ShadowsocksOutbound(**outbound_data)


def _convert_vmess(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[VmessOutbound]:
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
    if server.tls or server.meta.get("tls") or server.meta.get("servername") or server.meta.get("alpn"):
        outbound_data["tls"] = _convert_tls_config(server)
    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        outbound_data["transport"] = _convert_transport_config(server)
    return VmessOutbound(**outbound_data)


def _convert_vless(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[VlessOutbound]:
    """Convert ParsedServer to VlessOutbound."""
    outbound_data = {
        **base_data,
        "uuid": server.uuid or server.meta.get("uuid"),
        "flow": server.meta.get("flow")
    }
    # Add optional fields
    if server.meta.get("packet_encoding"):
        outbound_data["packet_encoding"] = server.meta["packet_encoding"]
    # Add TLS if present
    if server.tls or server.meta.get("tls") or server.meta.get("servername") or server.meta.get("alpn"):
        outbound_data["tls"] = _convert_tls_config(server)
    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        outbound_data["transport"] = _convert_transport_config(server)
    return VlessOutbound(**outbound_data)


def _convert_trojan(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[TrojanOutbound]:
    """Convert ParsedServer to TrojanOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password")
    }

    # Add optional fields
    if server.meta.get("fallback"):
        outbound_data["fallback"] = server.meta["fallback"]

    # Add TLS if present
    if server.tls or server.meta.get("tls") or server.meta.get("servername") or server.meta.get("alpn"):
        outbound_data["tls"] = _convert_tls_config(server)

    # Add transport if present
    if server.meta.get("network") in ["ws", "grpc", "http"]:
        outbound_data["transport"] = _convert_transport_config(server)

    return TrojanOutbound(**outbound_data)


def _convert_hysteria2(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[Hysteria2Outbound]:
    """Convert ParsedServer to Hysteria2Outbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password")
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

    # Add TLS if present
    if server.tls or server.meta.get("tls"):
        outbound_data["tls"] = _convert_tls_config(server)

    return Hysteria2Outbound(**outbound_data)


def _convert_wireguard(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[WireGuardOutbound]:
    """Convert ParsedServer to WireGuardOutbound."""
    outbound_data = {
        **base_data,
        "private_key": server.private_key or server.meta.get("private_key"),
        "peer_public_key": server.peer_public_key or server.meta.get("peer_public_key")
    }

    # Add optional fields
    if server.pre_shared_key or server.meta.get("pre_shared_key"):
        outbound_data["pre_shared_key"] = server.pre_shared_key or server.meta.get("pre_shared_key")
    if server.meta.get("mtu"):
        outbound_data["mtu"] = server.meta["mtu"]
    if server.meta.get("keepalive"):
        outbound_data["keepalive"] = server.meta["keepalive"]
    if server.local_address:
        outbound_data["local_address"] = server.local_address
    if server.meta.get("system_interface"):
        outbound_data["system_interface"] = server.meta["system_interface"]
    if server.meta.get("interface_name"):
        outbound_data["interface_name"] = server.meta["interface_name"]
    if server.meta.get("peers"):
        outbound_data["peers"] = server.meta["peers"]
    if server.meta.get("reserved"):
        outbound_data["reserved"] = server.meta["reserved"]

    return WireGuardOutbound(**outbound_data)


def _convert_tuic(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[TuicOutbound]:
    """Convert ParsedServer to TuicOutbound."""
    outbound_data = {
        **base_data,
        "uuid": server.uuid or server.meta.get("uuid"),
        "password": server.password or server.meta.get("password")
    }

    # Add optional fields
    if server.congestion_control or server.meta.get("congestion_control"):
        outbound_data["congestion_control"] = server.congestion_control or server.meta.get("congestion_control")
    if server.meta.get("zero_rtt_handshake"):
        outbound_data["zero_rtt_handshake"] = server.meta["zero_rtt_handshake"]
    if server.meta.get("udp_relay_mode"):
        outbound_data["udp_relay_mode"] = server.meta["udp_relay_mode"]
    if server.meta.get("heartbeat"):
        outbound_data["heartbeat"] = server.meta["heartbeat"]

    # Add TLS if present
    if server.tls or server.meta.get("tls"):
        outbound_data["tls"] = _convert_tls_config(server)

    return TuicOutbound(**outbound_data)


def _convert_shadowtls(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[ShadowTlsOutbound]:
    """Convert ParsedServer to ShadowTlsOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password")
    }

    # Add optional fields
    if server.version or server.meta.get("version"):
        outbound_data["version"] = server.version or server.meta.get("version")
    if server.handshake or server.meta.get("handshake"):
        outbound_data["handshake"] = server.handshake or server.meta.get("handshake")
    if server.meta.get("handshake_for_internal"):
        outbound_data["handshake_for_internal"] = server.meta["handshake_for_internal"]

    # Add TLS if present
    if server.tls or server.meta.get("tls"):
        outbound_data["tls"] = _convert_tls_config(server)

    return ShadowTlsOutbound(**outbound_data)


def _convert_anytls(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[AnyTlsOutbound]:
    """Convert ParsedServer to AnyTlsOutbound."""
    outbound_data = {
        **base_data,
        "password": server.password or server.meta.get("password")
    }

    # Add optional fields
    if server.meta.get("idle_session_check_interval"):
        outbound_data["idle_session_check_interval"] = server.meta["idle_session_check_interval"]
    if server.meta.get("idle_session_timeout"):
        outbound_data["idle_session_timeout"] = server.meta["idle_session_timeout"]
    if server.meta.get("min_idle_session"):
        outbound_data["min_idle_session"] = server.meta["min_idle_session"]

    return AnyTlsOutbound(**outbound_data)


def _convert_tor(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[TorOutbound]:
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


def _convert_ssh(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[SshOutbound]:
    """Convert ParsedServer to SshOutbound."""
    outbound_data = {
        **base_data,
        "user": server.username or server.meta.get("user")
    }

    # Add optional fields
    if server.password or server.meta.get("password"):
        outbound_data["password"] = server.password or server.meta.get("password")
    if server.private_key or server.meta.get("private_key"):
        outbound_data["private_key"] = server.private_key or server.meta.get("private_key")
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


def _convert_http(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[HttpOutbound]:
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


def _convert_socks(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[SocksOutbound]:
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


def _convert_direct(server: ParsedServer, base_data: Dict[str, Any]) -> Optional[DirectOutbound]:
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


def _convert_tls_config(server: ParsedServer) -> Optional[TlsConfig]:
    """Convert server TLS data to TlsConfig."""
    tls_data = {}

    # Use server.tls if available, otherwise extract from meta
    if server.tls:
        tls_data = server.tls
    else:
        # Extract TLS fields from meta
        if server.meta.get("tls"):
            tls_data["enabled"] = True
        if server.meta.get("servername"):
            tls_data["server_name"] = server.meta["servername"]
        if server.meta.get("alpn"):
            tls_data["alpn"] = server.meta["alpn"]
        if server.meta.get("insecure"):
            tls_data["insecure"] = server.meta["insecure"]
        if server.meta.get("reality"):
            tls_data["reality"] = server.meta["reality"]
        if server.meta.get("utls"):
            tls_data["utls"] = server.meta["utls"]

    return TlsConfig(**tls_data) if tls_data else None


def _convert_transport_config(server: ParsedServer) -> Optional[TransportConfig]:
    """Convert server transport data to TransportConfig."""
    transport_data = {}

    network = server.meta.get("network")
    if network in ["ws", "grpc", "http", "httpupgrade", "quic", "tcp", "udp"]:
        transport_data["network"] = network

        if network == "ws":
            if server.meta.get("ws_path"):
                transport_data["ws_opts"] = {"path": server.meta["ws_path"]}
            if server.meta.get("ws_headers"):
                transport_data["ws_opts"] = transport_data.get("ws_opts", {})
                transport_data["ws_opts"]["headers"] = server.meta["ws_headers"]
        elif network == "grpc":
            if server.meta.get("grpc_service_name"):
                transport_data["grpc_opts"] = {"serviceName": server.meta["grpc_service_name"]}
        elif network == "http":
            if server.meta.get("http_path"):
                transport_data["http_opts"] = {"path": server.meta["http_path"]}
            if server.meta.get("http_host"):
                transport_data["http_opts"] = transport_data.get("http_opts", {})
                transport_data["http_opts"]["host"] = server.meta["http_host"]

    return TransportConfig(**transport_data) if transport_data else None


def convert_client_profile_to_inbounds(profile: ClientProfile) -> List[Union[
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound
]]:
    """Convert ClientProfile to list of sing-box inbound models.

    Args:
        profile: ClientProfile object to convert

    Returns:
        List of inbound model instances

    """
    inbounds = []

    for inbound_profile in profile.inbounds:
        try:
            inbound_data = {
                "type": inbound_profile.type,
                "tag": inbound_profile.options.get("tag", f"{inbound_profile.type}-in") if inbound_profile.options else f"{inbound_profile.type}-in"
            }

            # Add listen fields
            if inbound_profile.listen:
                inbound_data["listen"] = inbound_profile.listen
            if inbound_profile.port:
                inbound_data["listen_port"] = inbound_profile.port

            # Add other options
            if inbound_profile.options:
                for key, value in inbound_profile.options.items():
                    if key not in ["tag", "listen", "port"]:
                        inbound_data[key] = value

            # Create appropriate inbound model
            if inbound_profile.type == "mixed":
                inbounds.append(MixedInbound(**inbound_data))
            elif inbound_profile.type == "socks":
                inbounds.append(SocksInbound(**inbound_data))
            elif inbound_profile.type == "http":
                inbounds.append(HttpInbound(**inbound_data))
            elif inbound_profile.type == "shadowsocks":
                inbounds.append(ShadowsocksInbound(**inbound_data))
            elif inbound_profile.type == "vmess":
                inbounds.append(VmessInbound(**inbound_data))
            elif inbound_profile.type == "vless":
                inbounds.append(VlessInbound(**inbound_data))
            elif inbound_profile.type == "trojan":
                inbounds.append(TrojanInbound(**inbound_data))
            elif inbound_profile.type == "hysteria2":
                inbounds.append(Hysteria2Inbound(**inbound_data))
            elif inbound_profile.type == "wireguard":
                inbounds.append(WireGuardInbound(**inbound_data))
            elif inbound_profile.type == "tuic":
                inbounds.append(TuicInbound(**inbound_data))
            elif inbound_profile.type == "shadowtls":
                inbounds.append(ShadowTlsInbound(**inbound_data))
            elif inbound_profile.type == "direct":
                inbounds.append(DirectInbound(**inbound_data))
            else:
                logger.warning(f"Unsupported inbound type: {inbound_profile.type}")

        except Exception as e:
            logger.error(f"Failed to convert inbound {inbound_profile.type}: {e}")

    return inbounds


@register("singbox_v2")
class SingboxExporterV2(BaseExporter):
    """New Sing-box configuration exporter using modular Pydantic models.

    This exporter provides better validation, type safety, and maintainability
    compared to the legacy exporter. It uses the modular Pydantic models
    from src.sboxmgr.models.singbox for full validation.
    """

    def export(self, servers: List[ParsedServer], client_profile: Optional[ClientProfile] = None) -> str:
        """Export servers to sing-box JSON configuration string.

        Args:
            servers: List of ParsedServer objects to export
            client_profile: Optional ClientProfile for inbound configuration

        Returns:
            JSON string containing sing-box configuration

        Raises:
            ValueError: If server data is invalid or cannot be exported

        """
        try:
            # Convert servers to outbounds
            outbounds = []
            for server in servers:
                outbound = convert_parsed_server_to_outbound(server)
                if outbound:
                    outbounds.append(outbound)

            # Add default outbounds
            outbounds.extend([
                DirectOutbound(type="direct", tag="direct"),
                BlockOutbound(type="block", tag="block")
            ])

            # Convert client profile to inbounds
            inbounds = []
            if client_profile:
                inbounds = convert_client_profile_to_inbounds(client_profile)

            # Create sing-box configuration
            config_data = {
                "log": LogConfig(level="info"),
                "inbounds": inbounds,
                "outbounds": outbounds,
                "route": RouteConfig(
                    rules=[
                        RouteRule(outbound="direct", network="tcp"),
                        RouteRule(outbound="direct", network="udp")
                    ],
                    final="direct"
                )
            }

            # Validate and export
            config = SingBoxConfig(**config_data)
            return config.to_json(indent=2)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ValueError(f"Failed to export configuration: {e}")
