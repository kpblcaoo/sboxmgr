"""Sing-box exporter v2 package.

This package provides a modern sing-box configuration exporter using modular
Pydantic models for better validation, type safety, and maintainability.

The package is organized into specialized modules:
- converter: Main conversion logic
- protocol_converters: Protocol-specific converters
- utils: Utility functions for TLS and transport
- inbound_converter: Inbound configuration conversion
- exporter: Main exporter class

Example usage:
    from sboxmgr.subscription.exporters.singbox_exporter_v2 import (
        convert_parsed_server_to_outbound,
        SingboxExporterV2
    )

    # Convert a single server
    outbound = convert_parsed_server_to_outbound(server)

    # Use the exporter
    exporter = SingboxExporterV2()
    config_json = exporter.export(servers, client_profile)
"""

# Main conversion functions
from .converter import convert_parsed_server_to_outbound

# Protocol converters
from .protocol_converters import (
    convert_shadowsocks, convert_vmess, convert_vless, convert_trojan,
    convert_hysteria2, convert_wireguard, convert_tuic, convert_shadowtls,
    convert_anytls, convert_tor, convert_ssh, convert_http, convert_socks,
    convert_direct
)

# Utils
from .utils import convert_tls_config, convert_transport_config

# Inbound converter
from .inbound_converter import convert_client_profile_to_inbounds

# Main exporter class
from .exporter import SingboxExporterV2

__all__ = [
    # Main converter
    "convert_parsed_server_to_outbound",

    # Protocol converters
    "convert_shadowsocks",
    "convert_vmess",
    "convert_vless",
    "convert_trojan",
    "convert_hysteria2",
    "convert_wireguard",
    "convert_tuic",
    "convert_shadowtls",
    "convert_anytls",
    "convert_tor",
    "convert_ssh",
    "convert_http",
    "convert_socks",
    "convert_direct",

    # Utils
    "convert_tls_config",
    "convert_transport_config",

    # Inbound converter
    "convert_client_profile_to_inbounds",

    # Main exporter
    "SingboxExporterV2",
]
