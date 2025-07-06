"""Sing-box exporter package.

This package provides modular sing-box configuration export functionality.
"""

from .config_processors import (
    create_base_outbound,
    normalize_protocol_type,
    process_standard_server,
)
from .constants import (
    CONFIG_WHITELIST,
    DEFAULT_URLTEST_CONFIG,
    PROTOCOL_NORMALIZATION,
    SUPPORTED_PROTOCOLS,
    TLS_CONFIG_FIELDS,
)
from .core import (
    create_modern_routing_rules,
    create_urltest_outbound,
    is_supported_protocol,
    process_single_server,
    singbox_export,
    singbox_export_with_middleware,
)
from .inbound_generator import generate_inbounds
from .protocol_handlers import (
    export_anytls,
    export_hysteria2,
    export_shadowtls,
    export_ssh,
    export_tor,
    export_tuic,
    export_wireguard,
    get_protocol_dispatcher,
)

# Main export functions
__all__ = [
    # Core functions
    "singbox_export",
    "singbox_export_with_middleware",
    "process_single_server",
    "is_supported_protocol",
    "create_urltest_outbound",
    "create_modern_routing_rules",
    # Inbound generation
    "generate_inbounds",
    # Protocol handlers
    "export_wireguard",
    "export_hysteria2",
    "export_tuic",
    "export_shadowtls",
    "export_anytls",
    "export_tor",
    "export_ssh",
    "get_protocol_dispatcher",
    # Config processors
    "normalize_protocol_type",
    "process_standard_server",
    "create_base_outbound",
    # Constants
    "SUPPORTED_PROTOCOLS",
    "PROTOCOL_NORMALIZATION",
    "CONFIG_WHITELIST",
    "DEFAULT_URLTEST_CONFIG",
    "TLS_CONFIG_FIELDS",
]
