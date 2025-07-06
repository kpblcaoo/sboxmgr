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

# Common models
from .common import MultiplexConfig, StreamSettings, TlsConfig

# Enums
from .enums import DomainStrategy, LogLevel, Network

# Outbound models
from .outbound_models import (
    BlockOutbound,
    DirectOutbound,
    DnsOutbound,
    HttpOutbound,
    HysteriaOutbound,
    OutboundBase,
    OutboundConfig,
    OutboundModel,
    ShadowsocksOutbound,
    SocksOutbound,
    TrojanOutbound,
    TuicOutbound,
    VlessOutbound,
    VmessOutbound,
    WireguardOutbound,
)

# Protocol configurations
from .protocol_configs import (
    ProtocolConfig,
    ShadowsocksConfig,
    TrojanConfig,
    TrojanUser,
    VlessConfig,
    VlessSettings,
    VlessUser,
    VmessConfig,
    VmessSettings,
    VmessUser,
    WireGuardConfig,
    WireGuardInterface,
    WireGuardPeer,
)

# Transport configurations
from .transport import (
    GrpcConfig,
    HttpConfig,
    QuicConfig,
    RealityConfig,
    UtlsConfig,
    WsConfig,
)

# Validators
from .validators import (
    convert_protocol_to_outbound,
    create_outbound_from_dict,
    generate_outbound_schema,
    generate_protocol_schema,
    validate_outbound_config,
    validate_protocol_config,
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
