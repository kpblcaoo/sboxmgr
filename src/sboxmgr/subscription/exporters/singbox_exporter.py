"""Sing-box exporter compatibility layer.

This module provides backward compatibility for the refactored sing-box exporter.
All functions are now imported from the modular singbox_exporter package.

For new code, consider importing directly from the singbox_exporter package modules.
"""

# Import all functions from the new modular structure
from .singbox_exporter import (  # Core export functions; Inbound generation; Protocol handlers; Config processors; Constants
    CONFIG_WHITELIST,
    DEFAULT_URLTEST_CONFIG,
    PROTOCOL_NORMALIZATION,
    SUPPORTED_PROTOCOLS,
    TLS_CONFIG_FIELDS,
    create_base_outbound,
    create_modern_routing_rules,
    create_urltest_outbound,
    export_anytls,
    export_hysteria2,
    export_shadowtls,
    export_ssh,
    export_tor,
    export_tuic,
    export_wireguard,
    generate_inbounds,
    get_protocol_dispatcher,
    is_supported_protocol,
    normalize_protocol_type,
    process_single_server,
    process_standard_server,
    singbox_export,
    singbox_export_with_middleware,
)

# Import legacy functions
from .singbox_exporter.legacy import (
    add_special_outbounds,
    create_enhanced_routing_rules,
    singbox_export_legacy,
)

# Backward compatibility aliases
_export_wireguard = export_wireguard
_export_hysteria2 = export_hysteria2
_export_tuic = export_tuic
_export_shadowtls = export_shadowtls
_export_anytls = export_anytls
_export_tor = export_tor
_export_ssh = export_ssh

_get_protocol_dispatcher = get_protocol_dispatcher
_normalize_protocol_type = normalize_protocol_type
_is_supported_protocol = is_supported_protocol
_create_base_outbound = create_base_outbound
_process_shadowsocks_config = (
    lambda o, s, m: process_standard_server(s, "shadowsocks") is not None
)
_process_transport_config = lambda o, m: None  # Handled internally now
_process_tls_config = lambda o, m, p: None  # Handled internally now
_process_auth_and_flow_config = lambda o, m: None  # Handled internally now
_process_tag_config = lambda o, s, m: None  # Handled internally now
_process_additional_config = lambda o, m: None  # Handled internally now
_process_standard_server = process_standard_server
_process_single_server = process_single_server
_create_modern_routing_rules = create_modern_routing_rules
_add_special_outbounds = add_special_outbounds
_create_enhanced_routing_rules = create_enhanced_routing_rules

# All public functions that were available in the original file
__all__ = [
    # Main export functions
    "singbox_export",
    "singbox_export_with_middleware",
    "singbox_export_legacy",
    "generate_inbounds",
    # Protocol handlers
    "export_wireguard",
    "export_hysteria2",
    "export_tuic",
    "export_shadowtls",
    "export_anytls",
    "export_tor",
    "export_ssh",
    # Internal functions (kept for compatibility)
    "_export_wireguard",
    "_export_hysteria2",
    "_export_tuic",
    "_export_shadowtls",
    "_export_anytls",
    "_export_tor",
    "_export_ssh",
    "_get_protocol_dispatcher",
    "_normalize_protocol_type",
    "_is_supported_protocol",
    "_create_base_outbound",
    "_process_shadowsocks_config",
    "_process_transport_config",
    "_process_tls_config",
    "_process_auth_and_flow_config",
    "_process_tag_config",
    "_process_additional_config",
    "_process_standard_server",
    "_process_single_server",
    "_create_modern_routing_rules",
    "_add_special_outbounds",
    "_create_enhanced_routing_rules",
    # Public utility functions
    "get_protocol_dispatcher",
    "normalize_protocol_type",
    "is_supported_protocol",
    "create_base_outbound",
    "process_standard_server",
    "process_single_server",
    "create_modern_routing_rules",
    "create_urltest_outbound",
    "add_special_outbounds",
    "create_enhanced_routing_rules",
    # Constants
    "SUPPORTED_PROTOCOLS",
    "PROTOCOL_NORMALIZATION",
    "CONFIG_WHITELIST",
    "DEFAULT_URLTEST_CONFIG",
    "TLS_CONFIG_FIELDS",
]
