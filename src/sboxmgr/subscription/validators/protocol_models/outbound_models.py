"""Outbound configuration models for sing-box export.

This module provides outbound configuration models for sing-box export format
including all supported protocols and their specific configurations.
"""

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from .common import MultiplexConfig, TlsConfig


# Base Outbound Model
class OutboundBase(BaseModel):
    """Base outbound configuration for sing-box export."""

    type: str = Field(..., description="Outbound type")
    tag: Optional[str] = Field(None, description="Outbound tag")
    server: Optional[str] = Field(None, description="Server address")
    server_port: Optional[int] = Field(None, ge=1, le=65535, description="Server port")
    tls: Optional[TlsConfig] = Field(None, description="TLS configuration")
    multiplex: Optional[MultiplexConfig] = Field(
        None, description="Multiplexing configuration"
    )
    local_address: Optional[list[str]] = Field(None, description="Local address list")

    class Config:
        extra = "forbid"


# Protocol-specific Outbound Models
class ShadowsocksOutbound(OutboundBase):
    """Shadowsocks outbound configuration for sing-box."""

    type: Literal["shadowsocks"] = "shadowsocks"
    method: str = Field(..., description="Encryption method")
    password: str = Field(..., description="Authentication password")
    plugin: Optional[str] = Field(None, description="Obfuscation plugin")
    plugin_opts: Optional[dict[str, Any]] = Field(None, description="Plugin options")


class VmessOutbound(OutboundBase):
    """VMess outbound configuration for sing-box."""

    type: Literal["vmess"] = "vmess"
    uuid: str = Field(..., description="User UUID")
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = (
        Field("auto", description="Encryption method")
    )
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(
        None, description="Packet encoding method"
    )


class VlessOutbound(OutboundBase):
    """VLESS outbound configuration for sing-box."""

    type: Literal["vless"] = "vless"
    uuid: str = Field(..., description="User UUID")
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = Field(
        None, description="Flow type for XTLS"
    )
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(
        None, description="Packet encoding method"
    )


class TrojanOutbound(OutboundBase):
    """Trojan outbound configuration for sing-box."""

    type: Literal["trojan"] = "trojan"
    password: str = Field(..., description="Authentication password")
    fallback: Optional[dict[str, Any]] = Field(
        None, description="Fallback configuration"
    )


class WireguardOutbound(OutboundBase):
    """WireGuard outbound configuration for sing-box."""

    type: Literal["wireguard"] = "wireguard"
    private_key: str = Field(..., description="Interface private key")
    peer_public_key: str = Field(..., description="Peer public key")
    mtu: Optional[int] = Field(0, ge=0, description="Maximum packet size")
    keepalive: Optional[bool] = Field(False, description="Enable keepalive")
    peers: Optional[list[dict[str, Any]]] = Field(None, description="Additional peers")
    reserved: Optional[list[int]] = Field(None, description="Reserved bytes")


class HysteriaOutbound(OutboundBase):
    """Hysteria outbound configuration for sing-box."""

    type: Literal["hysteria"] = "hysteria"
    up_mbps: Optional[int] = Field(None, ge=0, description="Upload speed in Mbps")
    down_mbps: Optional[int] = Field(None, ge=0, description="Download speed in Mbps")
    obfs: Optional[str] = Field(None, description="Obfuscation password")
    auth_str: Optional[str] = Field(None, description="Authentication string")


class TuicOutbound(OutboundBase):
    """TUIC outbound configuration for sing-box."""

    type: Literal["tuic"] = "tuic"
    uuid: str = Field(..., description="User UUID")
    password: str = Field(..., description="Authentication password")
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = Field(
        None, description="Congestion control algorithm"
    )
    zero_rtt_handshake: Optional[bool] = Field(
        None, description="Enable zero-RTT handshake"
    )


class HttpOutbound(OutboundBase):
    """HTTP outbound configuration for sing-box."""

    type: Literal["http"] = "http"
    username: Optional[str] = Field(None, description="HTTP username")
    password: Optional[str] = Field(None, description="HTTP password")
    path: Optional[str] = Field(None, description="HTTP path")


class SocksOutbound(OutboundBase):
    """SOCKS outbound configuration for sing-box."""

    type: Literal["socks"] = "socks"
    version: Optional[Literal["4", "4a", "5"]] = Field(
        None, description="SOCKS version"
    )
    username: Optional[str] = Field(None, description="SOCKS username")
    password: Optional[str] = Field(None, description="SOCKS password")


class DirectOutbound(OutboundBase):
    """Direct outbound configuration for sing-box."""

    type: Literal["direct"] = "direct"
    override_address: Optional[str] = Field(None, description="Override address")
    override_port: Optional[int] = Field(
        None, ge=0, le=65535, description="Override port"
    )


class BlockOutbound(OutboundBase):
    """Block outbound configuration for sing-box."""

    type: Literal["block"] = "block"


class DnsOutbound(OutboundBase):
    """DNS outbound configuration for sing-box."""

    type: Literal["dns"] = "dns"


# Union Type for all outbound models
OutboundModel = Union[
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
]


class OutboundConfig(BaseModel):
    """Outbound configuration model with discriminator."""

    outbound: OutboundModel = Field(..., discriminator="type")

    class Config:
        extra = "forbid"
