"""Inbound models for sing-box configuration."""

from typing import Any, Literal, Optional, Union

from pydantic import Field, field_validator

from .auth import AuthenticationUser
from .base import SingBoxModelBase
from .common import TlsConfig, TransportConfig
from .enums import Network


class InboundBase(SingBoxModelBase):
    """Base class for inbound configurations with universal fields."""

    type: str = Field(..., description="Inbound protocol type.")
    tag: Optional[str] = Field(default=None, description="Unique tag for the inbound.")
    listen: Optional[str] = Field(
        default=None, description="Listen address, e.g., '0.0.0.0'."
    )
    listen_port: Optional[int] = Field(
        default=None, ge=0, le=65535, description="Listen port."
    )
    tcp_fast_open: Optional[bool] = Field(
        default=None, description="Enable TCP Fast Open."
    )
    udp_fragment: Optional[bool] = Field(
        default=None, description="Enable UDP fragmentation."
    )
    tcp_multi_path: Optional[bool] = Field(
        default=None, description="Enable TCP Multi Path."
    )
    udp_timeout: Optional[str] = Field(
        default=None, description="UDP NAT expiration time."
    )
    detour: Optional[str] = Field(
        default=None, description="Forward connections to specified inbound."
    )

    model_config = {"extra": "forbid"}


class InboundWithUsers(InboundBase):
    """Base class for inbounds that support user authentication."""

    users: Optional[list[AuthenticationUser]] = Field(
        default=None, description="Users for authentication."
    )


class InboundWithGenericUsers(InboundBase):
    """Base class for inbounds that support generic user authentication."""

    users: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Users for authentication."
    )


class InboundWithTls(InboundWithUsers):
    """Base class for inbounds that support TLS."""

    tls: Optional[TlsConfig] = Field(default=None, description="TLS settings.")


class InboundWithTlsGenericUsers(InboundWithGenericUsers):
    """Base class for inbounds that support TLS with generic users."""

    tls: Optional[TlsConfig] = Field(default=None, description="TLS settings.")


class InboundWithTransport(InboundWithTls):
    """Base class for inbounds that support transport layer."""

    transport: Optional[TransportConfig] = Field(
        default=None, description="Transport layer settings."
    )


class InboundWithTransportGenericUsers(InboundWithTlsGenericUsers):
    """Base class for inbounds that support transport layer with generic users."""

    transport: Optional[TransportConfig] = Field(
        default=None, description="Transport layer settings."
    )


# Simple inbounds (no TLS, no transport)
class MixedInbound(InboundWithUsers):
    """Mixed inbound for HTTP and SOCKS."""

    type: Literal["mixed"] = Field(
        default="mixed", description="Mixed protocol (HTTP and SOCKS)."
    )
    set_system_proxy: Optional[bool] = Field(
        default=None, description="Set as system proxy."
    )


class SocksInbound(InboundWithUsers):
    """SOCKS inbound configuration."""

    type: Literal["socks"] = Field(
        default="socks", description="SOCKS protocol (v4/v5)."
    )
    udp: Optional[bool] = Field(default=None, description="Enable UDP support.")


class ShadowsocksInbound(InboundBase):
    """Shadowsocks inbound configuration."""

    type: Literal["shadowsocks"] = Field(
        default="shadowsocks", description="Shadowsocks protocol."
    )
    method: str = Field(..., description="Encryption method, e.g., 'aes-256-gcm'.")
    password: str = Field(..., description="Password for authentication.")
    network: Optional[Network] = Field(
        default=None, description="Network type (tcp, udp, or both)."
    )
    users: Optional[list[AuthenticationUser]] = Field(
        default=None, description="Users for multi-user mode."
    )

    @field_validator("method")
    def validate_method(cls, v):
        """Validate Shadowsocks encryption method."""
        valid_methods = ["aes-256-gcm", "chacha20-ietf-poly1305", "aes-128-gcm"]
        if v not in valid_methods:
            raise ValueError(f"Invalid method: {v}")
        return v


class Hysteria2Inbound(InboundBase):
    """Hysteria2 inbound configuration."""

    type: Literal["hysteria2"] = Field(
        default="hysteria2", description="Hysteria2 protocol."
    )
    password: Optional[str] = Field(
        default=None, description="Password for authentication."
    )
    up_mbps: Optional[int] = Field(
        default=None, ge=0, description="Upload bandwidth in Mbps."
    )
    down_mbps: Optional[int] = Field(
        default=None, ge=0, description="Download bandwidth in Mbps."
    )
    obfs: Optional[str] = Field(
        default=None, description="Obfuscation password, e.g., 'salamander'."
    )
    obfs_type: Optional[Literal["salamander"]] = Field(
        default=None, description="Obfuscation type for Hysteria2."
    )
    users: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Users with password."
    )


# TLS-only inbounds
class HttpInbound(InboundWithTls):
    """HTTP inbound configuration."""

    type: Literal["http"] = Field(default="http", description="HTTP protocol.")
    path: Optional[str] = Field(default=None, description="HTTP path for requests.")


class TrojanInbound(InboundWithTlsGenericUsers):
    """Trojan inbound configuration."""

    type: Literal["trojan"] = Field(default="trojan", description="Trojan protocol.")
    fallback: Optional[dict[str, Any]] = Field(
        default=None, description="Fallback settings, e.g., {'dest': '80'}."
    )


class TuicInbound(InboundWithTlsGenericUsers):
    """TUIC inbound configuration."""

    type: Literal["tuic"] = Field(default="tuic", description="TUIC protocol.")
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = Field(
        default=None, description="Congestion control algorithm."
    )
    zero_rtt_handshake: Optional[bool] = Field(
        default=None, description="Enable zero-RTT handshake."
    )


# TLS + Transport inbounds
class VmessInbound(InboundWithTransportGenericUsers):
    """VMess inbound configuration."""

    type: Literal["vmess"] = Field(default="vmess", description="VMess protocol.")


class VlessInbound(InboundWithTransportGenericUsers):
    """VLESS inbound configuration."""

    type: Literal["vless"] = Field(default="vless", description="VLESS protocol.")


# Special inbounds
class WireGuardInbound(InboundBase):
    """WireGuard inbound configuration."""

    type: Literal["wireguard"] = Field(
        default="wireguard", description="WireGuard protocol."
    )
    private_key: str = Field(..., description="Private key for WireGuard.")
    peer_public_key: str = Field(..., description="Public key of the peer.")
    mtu: Optional[int] = Field(
        default=0, ge=0, description="Maximum transmission unit (0 for auto)."
    )
    keepalive: Optional[bool] = Field(
        default=False, description="Enable persistent keepalive."
    )
    system_interface: Optional[bool] = Field(
        default=None, description="Use system WireGuard interface."
    )
    interface_name: Optional[str] = Field(
        default=None, description="Name of the WireGuard interface."
    )
    peers: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="List of peer configurations, e.g., [{'public_key': 'xyz', 'allowed_ips': ['0.0.0.0/0']}].",
    )


class ShadowTlsInbound(InboundWithTlsGenericUsers):
    """ShadowTLS inbound configuration."""

    type: Literal["shadowtls"] = Field(
        default="shadowtls", description="ShadowTLS protocol."
    )
    version: Optional[Literal[1, 2, 3]] = Field(
        default=None, description="ShadowTLS version (1, 2, or 3)."
    )
    password: Optional[str] = Field(
        default=None, description="Password for authentication."
    )
    handshake: Optional[dict[str, Any]] = Field(
        default=None,
        description="Handshake settings, e.g., {'server': 'example.com', 'port': 443}.",
    )


class DirectInbound(InboundBase):
    """Direct inbound configuration."""

    type: Literal["direct"] = Field(
        default="direct", description="Direct connection protocol."
    )
    override_address: Optional[str] = Field(
        default=None, description="Override destination address."
    )
    override_port: Optional[int] = Field(
        default=None, ge=0, le=65535, description="Override destination port."
    )


class AnyTlsInbound(InboundWithTlsGenericUsers):
    """AnyTLS inbound configuration."""

    type: Literal["anytls"] = Field(default="anytls", description="AnyTLS protocol.")
    users: list[dict[str, Any]] = Field(
        ..., description="AnyTLS users with name and password."
    )
    padding_scheme: Optional[list[str]] = Field(
        default=None, description="AnyTLS padding scheme line array."
    )


class NaiveInbound(InboundWithTlsGenericUsers):
    """Naive inbound configuration."""

    type: Literal["naive"] = Field(default="naive", description="Naive protocol.")
    network: Optional[Network] = Field(
        default=None, description="Listen network (tcp, udp, or both)."
    )
    users: list[dict[str, Any]] = Field(
        ..., description="Naive users with username and password."
    )


class RedirectInbound(InboundBase):
    """Redirect inbound configuration (Linux and macOS only)."""

    type: Literal["redirect"] = Field(
        default="redirect", description="Redirect protocol."
    )


class TproxyInbound(InboundBase):
    """TProxy inbound configuration (Linux only)."""

    type: Literal["tproxy"] = Field(default="tproxy", description="TProxy protocol.")
    network: Optional[Network] = Field(
        default=None, description="Listen network (tcp, udp, or both)."
    )


class TunInbound(InboundBase):
    """TUN inbound configuration (Linux, Windows, macOS only)."""

    type: Literal["tun"] = Field(default="tun", description="TUN protocol.")
    interface_name: Optional[str] = Field(
        default=None, description="Virtual device name."
    )
    address: Optional[list[str]] = Field(
        default=None, description="IPv4 and IPv6 prefix for the tun interface."
    )
    mtu: Optional[int] = Field(
        default=None, ge=0, description="Maximum transmission unit."
    )
    auto_route: Optional[bool] = Field(
        default=None, description="Enable automatic routing."
    )
    iproute2_table_index: Optional[int] = Field(
        default=None, description="IPRoute2 table index."
    )
    iproute2_rule_index: Optional[int] = Field(
        default=None, description="IPRoute2 rule index."
    )
    auto_redirect: Optional[bool] = Field(
        default=None, description="Enable automatic redirect."
    )
    auto_redirect_input_mark: Optional[str] = Field(
        default=None, description="Input mark for auto redirect."
    )
    auto_redirect_output_mark: Optional[str] = Field(
        default=None, description="Output mark for auto redirect."
    )
    loopback_address: Optional[list[str]] = Field(
        default=None, description="Loopback addresses."
    )
    strict_route: Optional[bool] = Field(
        default=None, description="Enable strict routing."
    )
    route_address: Optional[list[str]] = Field(
        default=None, description="Route addresses."
    )
    route_exclude_address: Optional[list[str]] = Field(
        default=None, description="Exclude addresses from routing."
    )
    route_address_set: Optional[list[str]] = Field(
        default=None, description="Route address sets."
    )
    route_exclude_address_set: Optional[list[str]] = Field(
        default=None, description="Exclude address sets from routing."
    )
    endpoint_independent_nat: Optional[bool] = Field(
        default=None, description="Enable endpoint independent NAT."
    )
    udp_timeout: Optional[str] = Field(
        default=None, description="UDP timeout duration."
    )
    stack: Optional[Literal["system", "gvisor"]] = Field(
        default=None, description="Network stack."
    )
    include_interface: Optional[list[str]] = Field(
        default=None, description="Include interfaces."
    )
    exclude_interface: Optional[list[str]] = Field(
        default=None, description="Exclude interfaces."
    )
    include_uid: Optional[list[int]] = Field(default=None, description="Include UIDs.")
    include_uid_range: Optional[list[str]] = Field(
        default=None, description="Include UID ranges."
    )
    exclude_uid: Optional[list[int]] = Field(default=None, description="Exclude UIDs.")
    exclude_uid_range: Optional[list[str]] = Field(
        default=None, description="Exclude UID ranges."
    )
    include_android_user: Optional[list[int]] = Field(
        default=None, description="Include Android users."
    )
    include_package: Optional[list[str]] = Field(
        default=None, description="Include packages."
    )
    exclude_package: Optional[list[str]] = Field(
        default=None, description="Exclude packages."
    )
    platform: Optional[dict[str, Any]] = Field(
        default=None, description="Platform-specific settings."
    )


# Union type for all inbound configurations
Inbound = Union[
    MixedInbound,
    SocksInbound,
    HttpInbound,
    ShadowsocksInbound,
    VmessInbound,
    VlessInbound,
    TrojanInbound,
    Hysteria2Inbound,
    WireGuardInbound,
    TuicInbound,
    ShadowTlsInbound,
    DirectInbound,
    AnyTlsInbound,
    NaiveInbound,
    RedirectInbound,
    TproxyInbound,
    TunInbound,
]
