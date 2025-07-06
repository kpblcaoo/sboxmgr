"""Sing-box configuration models.

This module contains Pydantic models for sing-box configuration format.
All models are strictly typed and validated against sing-box 1.11.13.
"""

# Authentication models
from .auth import AuthenticationConfig
from .auth import AuthenticationUser as User

# Common models
from .common import MultiplexConfig, TlsConfig, TransportConfig

# DNS models
from .dns import DnsConfig, DnsRule, DnsServer

# Enums
from .enums import DomainStrategy, LogLevel, Network

# Experimental models
from .experimental import ClashApiConfig, ExperimentalConfig, V2RayApiConfig

# Inbound models
from .inbounds import (
    AnyTlsInbound,
    DirectInbound,
    HttpInbound,
    Hysteria2Inbound,
    Inbound,
    InboundBase,
    MixedInbound,
    NaiveInbound,
    RedirectInbound,
    ShadowsocksInbound,
    ShadowTlsInbound,
    SocksInbound,
    TproxyInbound,
    TrojanInbound,
    TuicInbound,
    TunInbound,
    VlessInbound,
    VmessInbound,
    WireGuardInbound,
)

# Main config
from .main import LogConfig, SingBoxConfig

# NTP models
from .ntp import NtpConfig

# Observatory models
from .observatory import ObservatoryConfig

# Outbound models
from .outbounds import (
    AnyTlsOutbound,
    BlockOutbound,
    DirectOutbound,
    DnsOutbound,
    HttpOutbound,
    Hysteria2Outbound,
    HysteriaOutbound,
    Outbound,
    OutboundBase,
    SelectorOutbound,
    ShadowsocksOutbound,
    ShadowTlsOutbound,
    SocksOutbound,
    SshOutbound,
    TorOutbound,
    TrojanOutbound,
    TuicOutbound,
    UrlTestOutbound,
    VlessOutbound,
    VmessOutbound,
    WireGuardOutbound,
)

# Routing models
from .routing import RouteConfig, RouteRule

__all__ = [
    # Enums
    "LogLevel",
    "Network",
    "DomainStrategy",
    # Common
    "TlsConfig",
    "MultiplexConfig",
    "TransportConfig",
    # DNS
    "DnsConfig",
    "DnsServer",
    "DnsRule",
    # Auth
    "AuthenticationConfig",
    "User",
    # NTP
    "NtpConfig",
    # Inbounds
    "InboundBase",
    "MixedInbound",
    "SocksInbound",
    "HttpInbound",
    "ShadowsocksInbound",
    "VmessInbound",
    "VlessInbound",
    "TrojanInbound",
    "Hysteria2Inbound",
    "WireGuardInbound",
    "TuicInbound",
    "ShadowTlsInbound",
    "DirectInbound",
    "AnyTlsInbound",
    "NaiveInbound",
    "RedirectInbound",
    "TproxyInbound",
    "TunInbound",
    "Inbound",
    # Outbounds
    "OutboundBase",
    "ShadowsocksOutbound",
    "VmessOutbound",
    "VlessOutbound",
    "TrojanOutbound",
    "Hysteria2Outbound",
    "WireGuardOutbound",
    "HttpOutbound",
    "SocksOutbound",
    "TuicOutbound",
    "ShadowTlsOutbound",
    "DnsOutbound",
    "DirectOutbound",
    "BlockOutbound",
    "SelectorOutbound",
    "UrlTestOutbound",
    "HysteriaOutbound",
    "AnyTlsOutbound",
    "SshOutbound",
    "TorOutbound",
    "Outbound",
    # Routing
    "RouteConfig",
    "RouteRule",
    # Experimental
    "ExperimentalConfig",
    "ClashApiConfig",
    "V2RayApiConfig",
    # Observatory
    "ObservatoryConfig",
    # Main
    "SingBoxConfig",
    "LogConfig",
]
