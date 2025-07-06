"""Protocol-specific Pydantic models for subscription validation.

This module provides detailed validation models for various VPN protocols
including Shadowsocks, VMess, VLESS, Trojan, and others. These models
ensure proper validation of protocol-specific parameters and generate
accurate JSON schemas for configuration validation.

Implements ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation.

NOTE: This file has been refactored into a modular structure. This file now serves
as a compatibility layer. For new development, import from the protocol_models package directly.
"""

# Keep the original imports for backward compatibility
# Import all components from the new modular structure
from .protocol_models import *
from .protocol_models import (  # Enums; Transport; Common; Protocol configs; Outbound models; Validators
    BlockOutbound,
    DirectOutbound,
    DnsOutbound,
    DomainStrategy,
    GrpcConfig,
    HttpConfig,
    HttpOutbound,
    HysteriaOutbound,
    LogLevel,
    MultiplexConfig,
    Network,
    OutboundBase,
    OutboundConfig,
    OutboundModel,
    ProtocolConfig,
    QuicConfig,
    RealityConfig,
    ShadowsocksConfig,
    ShadowsocksOutbound,
    SocksOutbound,
    StreamSettings,
    TlsConfig,
    TrojanConfig,
    TrojanOutbound,
    TrojanUser,
    TuicOutbound,
    UtlsConfig,
    VlessConfig,
    VlessOutbound,
    VlessSettings,
    VlessUser,
    VmessConfig,
    VmessOutbound,
    VmessSettings,
    VmessUser,
    WireGuardConfig,
    WireGuardInterface,
    WireguardOutbound,
    WireGuardPeer,
    WsConfig,
    convert_protocol_to_outbound,
    create_outbound_from_dict,
    generate_outbound_schema,
    generate_protocol_schema,
    validate_outbound_config,
    validate_protocol_config,
)

# For backwards compatibility, keep the original variable names
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
