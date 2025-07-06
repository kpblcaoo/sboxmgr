"""Protocol-specific configuration models for VPN protocols.

This module provides detailed configuration models for specific VPN protocols
including Shadowsocks, VMess, VLESS, Trojan, and WireGuard.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .common import MultiplexConfig, StreamSettings, TlsConfig


# Shadowsocks
class ShadowsocksConfig(BaseModel):
    """Shadowsocks configuration for SOCKS5 proxy."""

    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    local_address: str = Field("127.0.0.1", description="Local address for proxy")
    local_port: int = Field(1080, ge=1, le=65535, description="Local port for proxy")
    password: str = Field(..., description="Authentication password")
    timeout: int = Field(300, ge=0, description="Connection timeout in seconds")
    method: str = Field(
        "aes-256-gcm",
        description="Encryption method (e.g., aes-256-gcm, chacha20-ietf-poly1305)",
    )
    fast_open: bool = Field(
        False, description="Enable TCP Fast Open for connection acceleration"
    )
    plugin: Optional[str] = Field(
        None, description="Obfuscation plugin (e.g., v2ray-plugin)"
    )
    plugin_opts: Optional[Dict[str, Any]] = Field(
        None, description="Plugin obfuscation parameters"
    )
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate allowed encryption methods."""
        valid_methods = [
            "aes-256-gcm",
            "chacha20-ietf-poly1305",
            "aes-128-gcm",
            "aes-256-cfb",
            "aes-128-cfb",
            "chacha20-ietf",
            "chacha20",
            "aes-256-ctr",
            "aes-128-ctr",
            "aes-192-ctr",
            "aes-256-ofb",
            "aes-128-ofb",
            "camellia-128-cfb",
            "camellia-192-cfb",
            "camellia-256-cfb",
            "bf-cfb",
            "rc4-md5",
            "salsa20",
        ]
        if v not in valid_methods:
            raise ValueError(f"Invalid encryption method: {v}")
        return v


# VMess
class VmessUser(BaseModel):
    """User for VMess protocol."""

    id: str = Field(..., description="User UUID for authentication")
    alterId: int = Field(
        0, ge=0, le=65535, description="Number of alternative IDs (0-65535)"
    )
    security: Optional[
        Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]
    ] = Field("auto", description="Encryption method")
    level: int = Field(0, ge=0, description="User level for access policy")
    email: Optional[str] = Field(None, description="Email for log identification")

    class Config:
        extra = "forbid"


class VmessSettings(BaseModel):
    """VMess protocol settings."""

    clients: List[VmessUser] = Field(
        ..., description="List of users for authentication"
    )
    detour: Optional[str] = Field(None, description="Tag for connection redirection")
    disableInsecureEncryption: bool = Field(
        False, description="Disable insecure encryption methods"
    )

    class Config:
        extra = "forbid"


class VmessConfig(BaseModel):
    """VMess configuration for V2Ray/Xray."""

    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    settings: VmessSettings = Field(..., description="User and policy settings")
    streamSettings: StreamSettings = Field(
        ..., description="Transport layer settings (TCP, WS, gRPC)"
    )
    multiplex: Optional[MultiplexConfig] = Field(
        None, description="Multiplexing settings"
    )
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"


# VLESS
class VlessUser(BaseModel):
    """User for VLESS protocol."""

    id: str = Field(..., description="User UUID for authentication")
    level: int = Field(0, ge=0, description="User level for access policy")
    email: Optional[str] = Field(None, description="Email for log identification")
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = Field(
        None, description="Flow type for XTLS"
    )

    class Config:
        extra = "forbid"


class VlessSettings(BaseModel):
    """VLESS protocol settings."""

    clients: List[VlessUser] = Field(
        ..., description="List of users for authentication"
    )
    decryption: str = Field("none", description="Decryption method (must be 'none')")
    fallbacks: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of fallback addresses for redirection"
    )

    class Config:
        extra = "forbid"


class VlessConfig(BaseModel):
    """VLESS configuration for Xray."""

    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    settings: VlessSettings = Field(..., description="User and fallback settings")
    streamSettings: StreamSettings = Field(
        ..., description="Transport layer settings (TCP, WS, gRPC)"
    )
    multiplex: Optional[MultiplexConfig] = Field(
        None, description="Multiplexing settings"
    )
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"


# Trojan
class TrojanUser(BaseModel):
    """User for Trojan protocol."""

    password: str = Field(..., description="Authentication password")

    class Config:
        extra = "forbid"


class TrojanConfig(BaseModel):
    """Trojan configuration for TLS proxy."""

    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    password: str = Field(..., description="Authentication password")
    tls: TlsConfig = Field(..., description="TLS settings for connection")
    multiplex: Optional[MultiplexConfig] = Field(
        None, description="Multiplexing settings"
    )
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")
    fallback: Optional[Dict[str, Any]] = Field(
        None, description="Fallback address for redirection"
    )

    class Config:
        extra = "forbid"


# WireGuard
class WireGuardPeer(BaseModel):
    """Peer for WireGuard protocol."""

    public_key: str = Field(..., description="Peer public key")
    allowed_ips: List[str] = Field(..., description="Allowed IP addresses for routing")
    endpoint: Optional[str] = Field(None, description="Peer address (IP:port)")
    persistent_keepalive: Optional[int] = Field(
        None, ge=0, description="Keepalive interval in seconds"
    )
    pre_shared_key: Optional[str] = Field(
        None, description="Pre-shared key for authentication"
    )

    class Config:
        extra = "forbid"


class WireGuardInterface(BaseModel):
    """Interface for WireGuard protocol."""

    private_key: str = Field(..., description="Interface private key")
    listen_port: Optional[int] = Field(
        None, ge=1, le=65535, description="Listening port"
    )
    fwmark: Optional[int] = Field(None, ge=0, description="Routing marker")
    address: Optional[List[str]] = Field(None, description="Interface IP addresses")
    mtu: Optional[int] = Field(
        0, ge=0, description="Maximum packet size (0 for auto-detection)"
    )
    dns: Optional[List[str]] = Field(None, description="DNS servers for interface")

    class Config:
        extra = "forbid"


class WireGuardConfig(BaseModel):
    """WireGuard configuration for VPN."""

    interface: WireGuardInterface = Field(
        ..., description="WireGuard interface settings"
    )
    peers: List[WireGuardPeer] = Field(..., description="List of peers for connection")
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"


# Protocol Union Type
ProtocolConfig = Union[
    ShadowsocksConfig, VmessConfig, VlessConfig, TrojanConfig, WireGuardConfig
]
