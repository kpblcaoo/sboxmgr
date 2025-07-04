"""
Configuration models for various proxy protocols.

This module contains Pydantic models for different proxy configuration formats:
- sing-box: Complete sing-box configuration models
- xray: Xray/V2Ray configuration models (planned)
- clash: Clash/Mihomo configuration models (planned)
"""

# Sing-box models
from .singbox import (
    # Main config
    SingBoxConfig,
    
    # Enums
    LogLevel, Network, DomainStrategy,
    
    # Common
    TlsConfig, MultiplexConfig, TransportConfig,
    # DNS
    DnsConfig, DnsServer, DnsRule,
    # Auth
    AuthenticationConfig, User,
    # NTP
    NtpConfig,
    # Inbounds
    InboundBase, MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound, Inbound,
    # Outbounds
    OutboundBase, ShadowsocksOutbound, VmessOutbound, VlessOutbound,
    TrojanOutbound, Hysteria2Outbound, WireGuardOutbound, HttpOutbound,
    SocksOutbound, TuicOutbound, ShadowTlsOutbound, DnsOutbound,
    DirectOutbound, BlockOutbound, SelectorOutbound, UrlTestOutbound,
    HysteriaOutbound, AnyTlsOutbound, SshOutbound, TorOutbound, Outbound,
    # Routing
    RouteConfig, RouteRule,
    # Experimental
    ExperimentalConfig, ClashApiConfig, V2RayApiConfig, CacheFileConfig,
    # Observatory
    ObservatoryConfig
)

# Утилиты (новые или совместимые с новой схемой)
# (Если нужны create_example_config, validate_config и т.д. — импортировать из singbox/utils.py или аналогичного файла)

__all__ = [
    # Sing-box models
    "SingBoxConfig", "LogLevel", "Network", "DomainStrategy",
    "TlsConfig", "MultiplexConfig", "TransportConfig",
    "DnsConfig", "DnsServer", "DnsRule",
    "AuthenticationConfig", "User", "NtpConfig", "InboundBase", 
    "MixedInbound", "SocksInbound", "HttpInbound", "ShadowsocksInbound",
    "VmessInbound", "VlessInbound", "TrojanInbound", "Hysteria2Inbound",
    "WireGuardInbound", "TuicInbound", "ShadowTlsInbound", "DirectInbound", "Inbound",
    "OutboundBase", "ShadowsocksOutbound", "VmessOutbound", "VlessOutbound", "TrojanOutbound",
    "Hysteria2Outbound", "WireGuardOutbound", "HttpOutbound", "SocksOutbound",
    "TuicOutbound", "ShadowTlsOutbound", "DnsOutbound", "DirectOutbound",
    "BlockOutbound", "SelectorOutbound", "UrlTestOutbound", "HysteriaOutbound",
    "AnyTlsOutbound", "SshOutbound", "TorOutbound", "Outbound", "RouteConfig",
    "RouteRule", "ExperimentalConfig", "ClashApiConfig", "V2RayApiConfig", "CacheFileConfig",
    "ObservatoryConfig"
] 