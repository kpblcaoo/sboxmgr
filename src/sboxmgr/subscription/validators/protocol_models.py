"""Protocol-specific Pydantic models for subscription validation.

This module provides detailed validation models for various VPN protocols
including Shadowsocks, VMess, VLESS, Trojan, and others. These models
ensure proper validation of protocol-specific parameters and generate
accurate JSON schemas for configuration validation.

Implements ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation.

NOTE: This file has been refactored into a modular structure. This file now serves
as a compatibility layer. For new development, import from the protocol_models package directly.
"""

# Import all components from the new modular structure
from .protocol_models import *

# Keep the original imports for backward compatibility
from .protocol_models import (
    # Enums
    LogLevel,
    DomainStrategy,
    Network,
    # Transport
    RealityConfig,
    UtlsConfig,
    WsConfig,
    HttpConfig,
    GrpcConfig,
    QuicConfig,
    # Common
    TlsConfig,
    StreamSettings,
    MultiplexConfig,
    # Protocol configs
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
    ProtocolConfig,
    # Outbound models
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
    OutboundConfig,
    # Validators
    validate_protocol_config,
    generate_protocol_schema,
    validate_outbound_config,
    generate_outbound_schema,
    convert_protocol_to_outbound,
    create_outbound_from_dict,
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
