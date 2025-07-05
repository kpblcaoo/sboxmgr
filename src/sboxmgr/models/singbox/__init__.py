"""Sing-box configuration models.

This module contains Pydantic models for sing-box configuration format.
All models are strictly typed and validated against sing-box 1.11.13.
"""

# Enums
from .enums import (
    LogLevel, Network, DomainStrategy
)

# Common models
from .common import (
    TlsConfig, MultiplexConfig, TransportConfig
)

# DNS models
from .dns import (
    DnsConfig, DnsServer, DnsRule
)

# Authentication models
from .auth import (
    AuthenticationConfig, AuthenticationUser as User
)

# NTP models
from .ntp import (
    NtpConfig
)

# Inbound models
from .inbounds import (
    InboundBase, MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound,
    AnyTlsInbound, NaiveInbound, RedirectInbound, TproxyInbound, TunInbound, Inbound
)

# Outbound models
from .outbounds import (
    OutboundBase, ShadowsocksOutbound, VmessOutbound, VlessOutbound,
    TrojanOutbound, Hysteria2Outbound, WireGuardOutbound, HttpOutbound,
    SocksOutbound, TuicOutbound, ShadowTlsOutbound, DnsOutbound,
    DirectOutbound, BlockOutbound, SelectorOutbound, UrlTestOutbound,
    HysteriaOutbound, AnyTlsOutbound, SshOutbound, TorOutbound, Outbound
)

# Routing models
from .routing import (
    RouteConfig, RouteRule
)

# Experimental models
from .experimental import (
    ExperimentalConfig, ClashApiConfig, V2RayApiConfig, CacheFileConfig
)

# Observatory models
from .observatory import (
    ObservatoryConfig
)

# Main config
from .main import SingBoxConfig, LogConfig

__all__ = [
    # Enums
    "LogLevel", "Network", "DomainStrategy",
    
    # Common
    "TlsConfig", "MultiplexConfig", "TransportConfig",
    
    # DNS
    "DnsConfig", "DnsServer", "DnsRule",
    
    # Auth
    "AuthenticationConfig", "User",
    
    # NTP
    "NtpConfig",
    
    # Inbounds
    "InboundBase", "MixedInbound", "SocksInbound", "HttpInbound", "ShadowsocksInbound",
    "VmessInbound", "VlessInbound", "TrojanInbound", "Hysteria2Inbound", "WireGuardInbound", 
    "TuicInbound", "ShadowTlsInbound", "DirectInbound", "AnyTlsInbound", "NaiveInbound", 
    "RedirectInbound", "TproxyInbound", "TunInbound", "Inbound",
    
    # Outbounds
    "OutboundBase", "ShadowsocksOutbound", "VmessOutbound", "VlessOutbound",
    "TrojanOutbound", "Hysteria2Outbound", "WireGuardOutbound", "HttpOutbound",
    "SocksOutbound", "TuicOutbound", "ShadowTlsOutbound", "DnsOutbound",
    "DirectOutbound", "BlockOutbound", "SelectorOutbound", "UrlTestOutbound",
    "HysteriaOutbound", "AnyTlsOutbound", "SshOutbound", "TorOutbound", "Outbound",
    
    # Routing
    "RouteConfig", "RouteRule",
    
    # Experimental
    "ExperimentalConfig", "ClashApiConfig", "V2RayApiConfig",
    
    # Observatory
    "ObservatoryConfig",
    
    # Main
    "SingBoxConfig", "LogConfig"
] 