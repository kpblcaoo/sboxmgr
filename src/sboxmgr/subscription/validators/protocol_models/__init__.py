"""Protocol models package for VPN protocols validation.

This package provides comprehensive Pydantic models for validating various VPN protocols
including Shadowsocks, VMess, VLESS, Trojan, and WireGuard configurations.

The package is organized into specialized modules:
- enums: Common enumeration types
- transport: Transport layer configurations
- common: Shared models across protocols
- protocol_configs: Protocol-specific configurations
- outbound_models: Outbound configurations for sing-box
- validators: Validation utilities and functions

Example usage:
    from sboxmgr.subscription.validators.protocol_models import (
        validate_protocol_config,
        ShadowsocksConfig,
        VmessConfig,
        OutboundModel
    )

    # Validate a protocol configuration
    config = validate_protocol_config(config_dict, "shadowsocks")
"""

# Enums
from .enums import LogLevel, DomainStrategy, Network

# Transport configurations
from .transport import (
    RealityConfig,
    UtlsConfig,
    WsConfig,
    HttpConfig,
    GrpcConfig,
    QuicConfig
)

# Common models
from .common import (
    TlsConfig,
    StreamSettings,
    MultiplexConfig
)

# Protocol configurations
from .protocol_configs import (
    ShadowsocksConfig,
    VmessUser,
    VmessSettings,
    VmessConfig,
    VlessUser,
    VlessSettings,
    VlessConfig,
    TrojanUser,
    TrojanConfig,
    WireGuardPeer,
    WireGuardInterface,
    WireGuardConfig,
    ProtocolConfig
)

# Outbound models
from .outbound_models import (
    OutboundBase,
    ShadowsocksOutbound,
    VmessOutbound,
    VlessOutbound,
    TrojanOutbound,
    WireguardOutbound,
    HysteriaOutbound,
    TuicOutbound,
    HttpOutbound,
    SocksOutbound,
    DirectOutbound,
    BlockOutbound,
    DnsOutbound,
    OutboundModel,
    OutboundConfig
)

# Validators
from .validators import (
    validate_protocol_config,
    generate_protocol_schema,
    validate_outbound_config,
    generate_outbound_schema,
    convert_protocol_to_outbound,
    create_outbound_from_dict
)

__all__ = [
    # Enums
    "LogLevel",
    "DomainStrategy",
    "Network",
    # Transport
    "RealityConfig",
    "UtlsConfig",
    "WsConfig",
    "HttpConfig",
    "GrpcConfig",
    "QuicConfig",
    # Common
    "TlsConfig",
    "StreamSettings",
    "MultiplexConfig",
    # Protocol configs
    "ShadowsocksConfig",
    "VmessUser",
    "VmessSettings",
    "VmessConfig",
    "VlessUser",
    "VlessSettings",
    "VlessConfig",
    "TrojanUser",
    "TrojanConfig",
    "WireGuardPeer",
    "WireGuardInterface",
    "WireGuardConfig",
    "ProtocolConfig",
    # Outbound models
    "OutboundBase",
    "ShadowsocksOutbound",
    "VmessOutbound",
    "VlessOutbound",
    "TrojanOutbound",
    "WireguardOutbound",
    "HysteriaOutbound",
    "TuicOutbound",
    "HttpOutbound",
    "SocksOutbound",
    "DirectOutbound",
    "BlockOutbound",
    "DnsOutbound",
    "OutboundModel",
    "OutboundConfig",
    # Validators
    "validate_protocol_config",
    "generate_protocol_schema",
    "validate_outbound_config",
    "generate_outbound_schema",
    "convert_protocol_to_outbound",
    "create_outbound_from_dict",
]
