"""Outbound models for sing-box configuration."""

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import Field, field_validator

from .base import SingBoxModelBase
from .common import MultiplexConfig, TlsConfig, TransportConfig
from .enums import DomainStrategy


class OutboundBase(SingBoxModelBase):
    """Base class for outbound configurations."""

    type: str = Field(
        ..., description="Outbound protocol type, e.g., 'shadowsocks', 'vmess'."
    )
    tag: Optional[str] = Field(default=None, description="Unique tag for the outbound.")
    server: Optional[str] = Field(
        default=None, description="Server address (IP or domain)."
    )
    server_port: Optional[int] = Field(
        default=None, ge=1, le=65535, description="Server port."
    )
    # tls: Optional[TlsConfig] = Field(
    #     default=None, description="TLS settings for secure connection."
    # )
    multiplex: Optional[MultiplexConfig] = Field(
        default=None, description="Multiplexing settings."
    )
    # local_address: Optional[list[str]] = Field(
    #     default=None, description="Local addresses to bind."
    # )
    domain_strategy: Optional[DomainStrategy] = Field(
        default=None, description="Domain resolution strategy."
    )

    model_config = {"extra": "allow"}  # Allow extra fields for protocol-specific params


class OutboundWithTransport(OutboundBase):
    """Base class for outbounds that support transport layer."""

    transport: Optional[TransportConfig] = Field(
        default=None, description="Transport layer settings."
    )


class OutboundWithTls(OutboundBase):
    """Base class for outbounds that support TLS."""

    tls: Optional[TlsConfig] = Field(
        default=None, description="TLS settings for secure connection."
    )


class ShadowsocksOutbound(OutboundWithTransport):
    """Shadowsocks outbound configuration."""

    type: Literal["shadowsocks"] = Field(
        default="shadowsocks", description="Shadowsocks protocol."
    )
    method: str = Field(..., description="Encryption method, e.g., 'aes-256-gcm'.")
    password: str = Field(..., description="Password for authentication.")
    plugin: Optional[str] = Field(
        default=None, description="Obfuscation plugin, e.g., 'v2ray-plugin'."
    )
    plugin_opts: Optional[dict[str, Any]] = Field(
        default=None, description="Plugin options, e.g., {'mode': 'websocket'}."
    )
    udp_over_tcp: Optional[bool] = Field(
        default=None, description="Enable UDP over TCP."
    )

    @field_validator("method")
    def validate_method(cls, v):
        """Validate Shadowsocks encryption method."""
        valid_methods = ["aes-256-gcm", "chacha20-ietf-poly1305", "aes-128-gcm"]
        if v not in valid_methods:
            raise ValueError(f"Invalid method: {v}")
        return v


class VmessOutbound(OutboundWithTransport, OutboundWithTls):
    """VMess outbound configuration."""

    type: Literal["vmess"] = Field(default="vmess", description="VMess protocol.")
    uuid: str = Field(..., description="User UUID for authentication.")
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = (
        Field(default="auto", description="Encryption method.")
    )
    alter_id: Optional[int] = Field(
        default=0, description="Alternative ID count (0-65535)."
    )
    global_padding: Optional[bool] = Field(
        default=None, description="Enable global padding for obfuscation."
    )
    authenticated_length: Optional[bool] = Field(
        default=None, description="Enable authenticated length for security."
    )
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(
        default=None, description="Packet encoding method."
    )


class VlessOutbound(OutboundWithTransport, OutboundWithTls):
    """VLESS outbound configuration."""

    type: Literal["vless"] = Field(default="vless", description="VLESS protocol.")
    uuid: str = Field(..., description="User UUID for authentication.")
    flow: Optional[Literal["xtls-rprx-vision", ""]] = Field(
        default=None, description="Flow type for XTLS, e.g., 'xtls-rprx-vision'."
    )
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(
        default=None, description="Packet encoding method."
    )


class TrojanOutbound(OutboundWithTransport, OutboundWithTls):
    """Trojan outbound configuration."""

    type: Literal["trojan"] = Field(default="trojan", description="Trojan protocol.")
    password: str = Field(..., description="Password for authentication.")
    fallback: Optional[dict[str, Any]] = Field(
        default=None, description="Fallback settings, e.g., {'dest': '80'}."
    )


class Hysteria2Outbound(OutboundWithTransport, OutboundWithTls):
    """Hysteria2 outbound configuration."""

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


class WireGuardOutbound(OutboundBase):
    """WireGuard outbound configuration."""

    type: Literal["wireguard"] = Field(
        default="wireguard", description="WireGuard protocol."
    )
    private_key: str = Field(..., description="Private key for WireGuard.")
    peer_public_key: str = Field(..., description="Public key of the peer.")
    pre_shared_key: Optional[str] = Field(
        default=None, description="Pre-shared key for authentication."
    )
    mtu: Optional[int] = Field(
        default=0, ge=0, description="Maximum transmission unit (0 for auto)."
    )
    keepalive: Optional[str] = Field(
        default=None, description="Persistent keepalive interval, e.g., '25s'."
    )
    peers: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="List of peer configurations, e.g., [{'public_key': 'xyz', 'allowed_ips': ['0.0.0.0/0']}].",
    )
    reserved: Optional[list[int]] = Field(
        default=None, description="Reserved bits for compatibility."
    )
    local_address: Optional[list[str]] = Field(
        default=None, description="Local addresses to bind."
    )
    system_interface: Optional[bool] = Field(
        default=None, description="Use system WireGuard interface."
    )
    interface_name: Optional[str] = Field(
        default=None, description="Name of the WireGuard interface."
    )


class HttpOutbound(OutboundBase):
    """HTTP outbound configuration."""

    type: Literal["http"] = Field(default="http", description="HTTP protocol.")
    username: Optional[str] = Field(
        default=None, description="Username for authentication."
    )
    password: Optional[str] = Field(
        default=None, description="Password for authentication."
    )
    path: Optional[str] = Field(default=None, description="HTTP path for requests.")


class SocksOutbound(OutboundBase):
    """SOCKS outbound configuration."""

    type: Literal["socks"] = Field(
        default="socks", description="SOCKS protocol (v4/v5)."
    )
    version: Optional[Literal["4", "4a", "5"]] = Field(
        default="5", description="SOCKS version."
    )
    username: Optional[str] = Field(
        default=None, description="Username for authentication."
    )
    password: Optional[str] = Field(
        default=None, description="Password for authentication."
    )


class TuicOutbound(OutboundWithTransport, OutboundWithTls):
    """TUIC outbound configuration."""

    type: Literal["tuic"] = Field(default="tuic", description="TUIC protocol.")
    uuid: str = Field(..., description="UUID for authentication.")
    password: str = Field(..., description="Password for authentication.")
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = Field(
        default=None, description="Congestion control algorithm."
    )
    zero_rtt_handshake: Optional[bool] = Field(
        default=None, description="Enable zero-RTT handshake."
    )
    udp_relay_mode: Optional[str] = Field(default=None, description="UDP relay mode.")
    heartbeat: Optional[str] = Field(default=None, description="Heartbeat interval.")


class ShadowTlsOutbound(OutboundWithTransport, OutboundWithTls):
    """ShadowTLS outbound configuration."""

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
    handshake_for_internal: Optional[dict[str, Any]] = Field(
        default=None, description="Internal handshake settings."
    )


class DnsOutbound(OutboundBase):
    """DNS outbound configuration."""

    type: Literal["dns"] = Field(default="dns", description="DNS protocol.")


class DirectOutbound(OutboundBase):
    """Direct outbound configuration."""

    type: Literal["direct"] = Field(
        default="direct", description="Direct connection protocol."
    )
    override_address: Optional[str] = Field(
        default=None, description="Override destination address."
    )
    override_port: Optional[int] = Field(
        default=None, ge=0, le=65535, description="Override destination port."
    )
    proxy: Optional[str] = Field(default=None, description="Proxy outbound tag.")


class BlockOutbound(OutboundBase):
    """Block outbound configuration."""

    type: Literal["block"] = Field(
        default="block", description="Block connection protocol."
    )


class SelectorOutbound(OutboundBase):
    """Selector outbound configuration."""

    type: Literal["selector"] = Field(
        default="selector", description="Selector for outbound switching."
    )
    outbounds: list[str] = Field(
        ..., description="List of outbound tags to select from."
    )
    default: Optional[str] = Field(default=None, description="Default outbound tag.")


class UrlTestOutbound(OutboundBase):
    """URLTest outbound configuration."""

    type: Literal["urltest"] = Field(
        default="urltest", description="URLTest for automatic outbound selection."
    )
    outbounds: list[str] = Field(..., description="List of outbound tags to test.")
    url: str = Field(
        ...,
        description="URL for latency testing, e.g., 'http://www.google.com/generate_204'.",
    )
    interval: Union[int, str] = Field(
        ..., description="Test interval in seconds or duration string."
    )
    tolerance: Optional[int] = Field(
        default=None, ge=0, description="Latency tolerance in milliseconds."
    )
    idle_timeout: Optional[Union[int, str]] = Field(
        default=None, description="Idle timeout in seconds or duration string."
    )
    interrupt_exist_connections: Optional[bool] = Field(
        default=None,
        description="Interrupt existing connections when switching outbounds.",
    )


class HysteriaOutbound(OutboundBase):
    """Hysteria outbound configuration (legacy version)."""

    type: Literal["hysteria"] = Field(
        default="hysteria", description="Hysteria protocol (legacy)."
    )
    up_mbps: Optional[int] = Field(None, ge=0, description="Upload speed in Mbps.")
    down_mbps: Optional[int] = Field(None, ge=0, description="Download speed in Mbps.")
    obfs: Optional[str] = Field(None, description="Obfuscation password.")
    auth_str: Optional[str] = Field(None, description="Authentication string.")
    recv_window_conn: Optional[int] = Field(
        None, ge=0, description="QUIC stream-level flow control window."
    )
    recv_window: Optional[int] = Field(
        None, ge=0, description="QUIC connection-level flow control window."
    )
    disable_mtu_discovery: Optional[bool] = Field(
        None, description="Disable Path MTU Discovery."
    )


class AnyTlsOutbound(OutboundBase):
    """AnyTLS outbound configuration."""

    type: Literal["anytls"] = Field(default="anytls", description="AnyTLS protocol.")
    password: str = Field(..., description="AnyTLS password.")
    idle_session_check_interval: Optional[str] = Field(
        None, description="Interval checking for idle sessions."
    )
    idle_session_timeout: Optional[str] = Field(
        None, description="Timeout for idle sessions."
    )
    min_idle_session: Optional[int] = Field(
        None, ge=0, description="Minimum idle sessions to keep."
    )


class SshOutbound(OutboundBase):
    """SSH outbound configuration."""

    type: Literal["ssh"] = Field(default="ssh", description="SSH protocol.")
    user: Optional[str] = Field(None, description="SSH user.")
    password: Optional[str] = Field(None, description="SSH password.")
    private_key: Optional[str] = Field(None, description="Private key content.")
    private_key_path: Optional[str] = Field(None, description="Private key file path.")
    private_key_passphrase: Optional[str] = Field(
        None, description="Private key passphrase."
    )
    host_key: Optional[list[str]] = Field(None, description="Host key list.")
    host_key_algorithms: Optional[list[str]] = Field(
        None, description="Host key algorithms."
    )
    client_version: Optional[str] = Field(None, description="Client version string.")


class TorOutbound(OutboundBase):
    """Tor outbound configuration."""

    type: Literal["tor"] = Field(default="tor", description="Tor protocol.")
    executable_path: Optional[str] = Field(None, description="Path to Tor executable.")
    extra_args: Optional[list[str]] = Field(
        None, description="Extra arguments for Tor."
    )
    data_directory: Optional[str] = Field(None, description="Tor data directory.")
    torrc: Optional[dict[str, Any]] = Field(
        None, description="Tor configuration options."
    )


Outbound = Annotated[
    Union[
        ShadowsocksOutbound,
        VmessOutbound,
        VlessOutbound,
        TrojanOutbound,
        Hysteria2Outbound,
        WireGuardOutbound,
        HttpOutbound,
        SocksOutbound,
        TuicOutbound,
        ShadowTlsOutbound,
        DnsOutbound,
        DirectOutbound,
        BlockOutbound,
        SelectorOutbound,
        UrlTestOutbound,
        HysteriaOutbound,
        AnyTlsOutbound,
        SshOutbound,
        TorOutbound,
    ],
    Field(discriminator="type"),
]
