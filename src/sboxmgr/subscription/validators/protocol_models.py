"""Protocol-specific Pydantic models for subscription validation.

This module provides detailed validation models for various VPN protocols
including Shadowsocks, VMess, VLESS, Trojan, and others. These models
ensure proper validation of protocol-specific parameters and generate
accurate JSON schemas for configuration validation.

Implements ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum

# Common Enums
class LogLevel(str, Enum):
    """Logging levels for clients."""
    trace = "trace"
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"
    panic = "panic"

class DomainStrategy(str, Enum):
    """Domain resolution strategy."""
    prefer_ipv4 = "prefer_ipv4"
    prefer_ipv6 = "prefer_ipv6"
    ipv4_only = "ipv4_only"
    ipv6_only = "ipv6_only"

class Network(str, Enum):
    """Network type for connections."""
    tcp = "tcp"
    udp = "udp"
    tcp_udp = "tcp,udp"

# Detailed Obfuscation Models
class RealityConfig(BaseModel):
    """Reality protocol configuration for SNI protection."""
    public_key: str = Field(..., description="Reality public key")
    short_id: Optional[str] = Field(None, description="Reality short ID")
    max_time_difference: Optional[int] = Field(None, ge=0, description="Maximum time difference in seconds")
    fingerprint: Optional[str] = Field(None, description="Browser fingerprint")

    class Config:
        extra = "forbid"

class UtlsConfig(BaseModel):
    """uTLS configuration for TLS client emulation."""
    enabled: bool = Field(True, description="Enable uTLS")
    fingerprint: Optional[Literal["chrome", "firefox", "safari", "ios", "android", "edge", "360", "qq", "random", "randomized"]] = Field(None, description="Browser fingerprint to emulate")

    class Config:
        extra = "forbid"

class WsConfig(BaseModel):
    """WebSocket transport configuration."""
    path: str = Field(..., description="WebSocket path")
    headers: Optional[Dict[str, str]] = Field(None, description="WebSocket headers")
    max_early_data: Optional[int] = Field(None, ge=0, description="Maximum early data size")
    use_browser_forwarding: Optional[bool] = Field(None, description="Use browser forwarding")

    class Config:
        extra = "forbid"

class HttpConfig(BaseModel):
    """HTTP/2 transport configuration."""
    host: List[str] = Field(..., description="HTTP host list")
    path: str = Field(..., description="HTTP path")

    class Config:
        extra = "forbid"

class GrpcConfig(BaseModel):
    """gRPC transport configuration."""
    service_name: str = Field(..., description="gRPC service name")
    multi_mode: Optional[bool] = Field(None, description="Enable multi mode")
    idle_timeout: Optional[int] = Field(None, ge=0, description="Idle timeout in seconds")
    health_check_timeout: Optional[int] = Field(None, ge=0, description="Health check timeout in seconds")
    permit_without_stream: Optional[bool] = Field(None, description="Permit without stream")
    initial_windows_size: Optional[int] = Field(None, ge=0, description="Initial window size")

    class Config:
        extra = "forbid"

class QuicConfig(BaseModel):
    """QUIC transport configuration."""
    security: Literal["none", "tls"] = Field("none", description="QUIC security type")
    key: Optional[str] = Field(None, description="QUIC key")
    certificate: Optional[str] = Field(None, description="QUIC certificate")

    class Config:
        extra = "forbid"

# Common Models
class TlsConfig(BaseModel):
    """TLS configuration for protocols with detailed obfuscation models."""
    enabled: Optional[bool] = Field(True, description="Enable TLS for connection")
    server_name: Optional[str] = Field(None, description="SNI for TLS connection")
    alpn: Optional[List[str]] = Field(None, description="ALPN protocols list (e.g., h2, http/1.1)")
    min_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Minimum TLS version")
    max_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Maximum TLS version")
    certificate_path: Optional[str] = Field(None, description="Path to certificate file")
    key_path: Optional[str] = Field(None, description="Path to key file")
    certificate: Optional[str] = Field(None, description="Certificate content in PEM format")
    key: Optional[str] = Field(None, description="Key content in PEM format")
    allow_insecure: Optional[bool] = Field(False, description="Allow insecure connections (not recommended)")
    ech: Optional[Dict[str, Any]] = Field(None, description="ECH settings for SNI protection")
    utls: Optional[UtlsConfig] = Field(None, description="uTLS settings for TLS client emulation")
    reality: Optional[RealityConfig] = Field(None, description="Reality settings for SNI protection")

    class Config:
        extra = "forbid"

class StreamSettings(BaseModel):
    """Transport layer settings with detailed configuration models."""
    network: Optional[Literal["tcp", "udp", "ws", "http", "grpc", "quic"]] = Field(None, description="Transport type (TCP, WebSocket, gRPC, etc.)")
    security: Optional[Literal["none", "tls", "reality"]] = Field(None, description="Encryption type (TLS, REALITY or none)")
    tls_settings: Optional[TlsConfig] = Field(None, description="TLS settings for transport")
    ws_settings: Optional[WsConfig] = Field(None, description="WebSocket settings")
    http_settings: Optional[HttpConfig] = Field(None, description="HTTP/2 settings")
    grpc_settings: Optional[GrpcConfig] = Field(None, description="gRPC settings")
    quic_settings: Optional[QuicConfig] = Field(None, description="QUIC settings")

    class Config:
        extra = "forbid"

class MultiplexConfig(BaseModel):
    """Multiplexing configuration."""
    enabled: Optional[bool] = Field(None, description="Enable multiplexing")
    protocol: Optional[Literal["smux", "yamux", "h2mux"]] = Field(None, description="Multiplexing protocol")
    max_connections: Optional[int] = Field(None, ge=1, description="Maximum number of connections")
    min_streams: Optional[int] = Field(None, ge=0, description="Minimum number of streams")
    max_streams: Optional[int] = Field(None, ge=0, description="Maximum number of streams")
    padding: Optional[bool] = Field(None, description="Enable padding for obfuscation")

    class Config:
        extra = "forbid"

# Shadowsocks
class ShadowsocksConfig(BaseModel):
    """Shadowsocks configuration for SOCKS5 proxy."""
    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    local_address: str = Field("127.0.0.1", description="Local address for proxy")
    local_port: int = Field(1080, ge=1, le=65535, description="Local port for proxy")
    password: str = Field(..., description="Authentication password")
    timeout: int = Field(300, ge=0, description="Connection timeout in seconds")
    method: str = Field("aes-256-gcm", description="Encryption method (e.g., aes-256-gcm, chacha20-ietf-poly1305)")
    fast_open: bool = Field(False, description="Enable TCP Fast Open for connection acceleration")
    plugin: Optional[str] = Field(None, description="Obfuscation plugin (e.g., v2ray-plugin)")
    plugin_opts: Optional[Dict[str, Any]] = Field(None, description="Plugin obfuscation parameters")
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate allowed encryption methods."""
        valid_methods = [
            "aes-256-gcm", "chacha20-ietf-poly1305", "aes-128-gcm",
            "aes-256-cfb", "aes-128-cfb", "chacha20-ietf", "chacha20",
            "aes-256-ctr", "aes-128-ctr", "aes-192-ctr", "aes-256-ofb",
            "aes-128-ofb", "camellia-128-cfb", "camellia-192-cfb",
            "camellia-256-cfb", "bf-cfb", "rc4-md5", "salsa20"
        ]
        if v not in valid_methods:
            raise ValueError(f"Invalid encryption method: {v}")
        return v

# VMess
class VmessUser(BaseModel):
    """User for VMess protocol."""
    id: str = Field(..., description="User UUID for authentication")
    alterId: int = Field(0, ge=0, le=65535, description="Number of alternative IDs (0-65535)")
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = Field("auto", description="Encryption method")
    level: int = Field(0, ge=0, description="User level for access policy")
    email: Optional[str] = Field(None, description="Email for log identification")

    class Config:
        extra = "forbid"

class VmessSettings(BaseModel):
    """VMess protocol settings."""
    clients: List[VmessUser] = Field(..., description="List of users for authentication")
    detour: Optional[str] = Field(None, description="Tag for connection redirection")
    disableInsecureEncryption: bool = Field(False, description="Disable insecure encryption methods")

    class Config:
        extra = "forbid"

class VmessConfig(BaseModel):
    """VMess configuration for V2Ray/Xray."""
    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    settings: VmessSettings = Field(..., description="User and policy settings")
    streamSettings: StreamSettings = Field(..., description="Transport layer settings (TCP, WS, gRPC)")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Multiplexing settings")
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"

# VLESS
class VlessUser(BaseModel):
    """User for VLESS protocol."""
    id: str = Field(..., description="User UUID for authentication")
    level: int = Field(0, ge=0, description="User level for access policy")
    email: Optional[str] = Field(None, description="Email for log identification")
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = Field(None, description="Flow type for XTLS")

    class Config:
        extra = "forbid"

class VlessSettings(BaseModel):
    """VLESS protocol settings."""
    clients: List[VlessUser] = Field(..., description="List of users for authentication")
    decryption: str = Field("none", description="Decryption method (must be 'none')")
    fallbacks: Optional[List[Dict[str, Any]]] = Field(None, description="List of fallback addresses for redirection")

    class Config:
        extra = "forbid"

class VlessConfig(BaseModel):
    """VLESS configuration for Xray."""
    server: str = Field(..., description="Server address (IP or domain)")
    server_port: int = Field(..., ge=1, le=65535, description="Server port")
    settings: VlessSettings = Field(..., description="User and fallback settings")
    streamSettings: StreamSettings = Field(..., description="Transport layer settings (TCP, WS, gRPC)")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Multiplexing settings")
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
    multiplex: Optional[MultiplexConfig] = Field(None, description="Multiplexing settings")
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")
    fallback: Optional[Dict[str, Any]] = Field(None, description="Fallback address for redirection")

    class Config:
        extra = "forbid"

# WireGuard
class WireGuardPeer(BaseModel):
    """Peer for WireGuard protocol."""
    public_key: str = Field(..., description="Peer public key")
    allowed_ips: List[str] = Field(..., description="Allowed IP addresses for routing")
    endpoint: Optional[str] = Field(None, description="Peer address (IP:port)")
    persistent_keepalive: Optional[int] = Field(None, ge=0, description="Keepalive interval in seconds")
    pre_shared_key: Optional[str] = Field(None, description="Pre-shared key for authentication")

    class Config:
        extra = "forbid"

class WireGuardInterface(BaseModel):
    """Interface for WireGuard protocol."""
    private_key: str = Field(..., description="Interface private key")
    listen_port: Optional[int] = Field(None, ge=1, le=65535, description="Listening port")
    fwmark: Optional[int] = Field(None, ge=0, description="Routing marker")
    address: Optional[List[str]] = Field(None, description="Interface IP addresses")
    mtu: Optional[int] = Field(0, ge=0, description="Maximum packet size (0 for auto-detection)")
    dns: Optional[List[str]] = Field(None, description="DNS servers for interface")

    class Config:
        extra = "forbid"

class WireGuardConfig(BaseModel):
    """WireGuard configuration for VPN."""
    interface: WireGuardInterface = Field(..., description="WireGuard interface settings")
    peers: List[WireGuardPeer] = Field(..., description="List of peers for connection")
    udp: Optional[bool] = Field(True, description="Enable UDP traffic")

    class Config:
        extra = "forbid"

# Protocol Union Type
ProtocolConfig = Union[
    ShadowsocksConfig,
    VmessConfig,
    VlessConfig,
    TrojanConfig,
    WireGuardConfig
]

# Outbound Models for Export (sing-box format)
class OutboundBase(BaseModel):
    """Base outbound configuration for sing-box export."""
    type: str = Field(..., description="Outbound type")
    tag: Optional[str] = Field(None, description="Outbound tag")
    server: Optional[str] = Field(None, description="Server address")
    server_port: Optional[int] = Field(None, ge=1, le=65535, description="Server port")
    tls: Optional[TlsConfig] = Field(None, description="TLS configuration")
    multiplex: Optional[MultiplexConfig] = Field(None, description="Multiplexing configuration")
    local_address: Optional[List[str]] = Field(None, description="Local address list")

    class Config:
        extra = "forbid"

class ShadowsocksOutbound(OutboundBase):
    """Shadowsocks outbound configuration for sing-box."""
    type: Literal["shadowsocks"] = "shadowsocks"
    method: str = Field(..., description="Encryption method")
    password: str = Field(..., description="Authentication password")
    plugin: Optional[str] = Field(None, description="Obfuscation plugin")
    plugin_opts: Optional[Dict[str, Any]] = Field(None, description="Plugin options")

class VmessOutbound(OutboundBase):
    """VMess outbound configuration for sing-box."""
    type: Literal["vmess"] = "vmess"
    uuid: str = Field(..., description="User UUID")
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = Field("auto", description="Encryption method")
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(None, description="Packet encoding method")

class VlessOutbound(OutboundBase):
    """VLESS outbound configuration for sing-box."""
    type: Literal["vless"] = "vless"
    uuid: str = Field(..., description="User UUID")
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = Field(None, description="Flow type for XTLS")
    packet_encoding: Optional[Literal["packet", "xudp"]] = Field(None, description="Packet encoding method")

class TrojanOutbound(OutboundBase):
    """Trojan outbound configuration for sing-box."""
    type: Literal["trojan"] = "trojan"
    password: str = Field(..., description="Authentication password")
    fallback: Optional[Dict[str, Any]] = Field(None, description="Fallback configuration")

class WireguardOutbound(OutboundBase):
    """WireGuard outbound configuration for sing-box."""
    type: Literal["wireguard"] = "wireguard"
    private_key: str = Field(..., description="Interface private key")
    peer_public_key: str = Field(..., description="Peer public key")
    mtu: Optional[int] = Field(0, ge=0, description="Maximum packet size")
    keepalive: Optional[bool] = Field(False, description="Enable keepalive")
    peers: Optional[List[Dict[str, Any]]] = Field(None, description="Additional peers")
    reserved: Optional[List[int]] = Field(None, description="Reserved bytes")

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
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = Field(None, description="Congestion control algorithm")
    zero_rtt_handshake: Optional[bool] = Field(None, description="Enable zero-RTT handshake")

class HttpOutbound(OutboundBase):
    """HTTP outbound configuration for sing-box."""
    type: Literal["http"] = "http"
    username: Optional[str] = Field(None, description="HTTP username")
    password: Optional[str] = Field(None, description="HTTP password")
    path: Optional[str] = Field(None, description="HTTP path")

class SocksOutbound(OutboundBase):
    """SOCKS outbound configuration for sing-box."""
    type: Literal["socks"] = "socks"
    version: Optional[Literal["4", "4a", "5"]] = Field(None, description="SOCKS version")
    username: Optional[str] = Field(None, description="SOCKS username")
    password: Optional[str] = Field(None, description="SOCKS password")

class DirectOutbound(OutboundBase):
    """Direct outbound configuration for sing-box."""
    type: Literal["direct"] = "direct"
    override_address: Optional[str] = Field(None, description="Override address")
    override_port: Optional[int] = Field(None, ge=0, le=65535, description="Override port")

class BlockOutbound(OutboundBase):
    """Block outbound configuration for sing-box."""
    type: Literal["block"] = "block"

class DnsOutbound(OutboundBase):
    """DNS outbound configuration for sing-box."""
    type: Literal["dns"] = "dns"

# Unified Outbound Model with Discriminator
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
    DnsOutbound
]

# Create a model that uses the union with discriminator
class OutboundConfig(BaseModel):
    """Outbound configuration model with discriminator."""
    outbound: OutboundModel = Field(..., discriminator="type")

    class Config:
        extra = "forbid"

# Validation Functions
def validate_protocol_config(config: Dict[str, Any], protocol: str) -> ProtocolConfig:
    """Validate protocol-specific configuration.
    
    Args:
        config: Configuration dictionary
        protocol: Protocol type (shadowsocks, vmess, vless, trojan, wireguard)
        
    Returns:
        Validated protocol configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    protocol_map = {
        "shadowsocks": ShadowsocksConfig,
        "ss": ShadowsocksConfig,
        "vmess": VmessConfig,
        "vless": VlessConfig,
        "trojan": TrojanConfig,
        "wireguard": WireGuardConfig,
        "wg": WireGuardConfig
    }
    
    if protocol not in protocol_map:
        raise ValueError(f"Unsupported protocol: {protocol}")
    
    config_class = protocol_map[protocol]
    return config_class(**config)

def generate_protocol_schema(protocol: str) -> Dict[str, Any]:
    """Generate JSON schema for protocol configuration.
    
    Args:
        protocol: Protocol type
        
    Returns:
        JSON schema dictionary
    """
    protocol_map = {
        "shadowsocks": ShadowsocksConfig,
        "ss": ShadowsocksConfig,
        "vmess": VmessConfig,
        "vless": VlessConfig,
        "trojan": TrojanConfig,
        "wireguard": WireGuardConfig,
        "wg": WireGuardConfig
    }
    
    if protocol not in protocol_map:
        raise ValueError(f"Unsupported protocol: {protocol}")
    
    return protocol_map[protocol].model_json_schema()

def validate_outbound_config(config: Dict[str, Any]) -> OutboundModel:
    """Validate outbound configuration using unified OutboundModel.
    
    Args:
        config: Outbound configuration dictionary
        
    Returns:
        Validated outbound configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        # Try to create the appropriate outbound type based on discriminator
        outbound_type = config.get("type")
        if not outbound_type:
            raise ValueError("Outbound configuration must have a 'type' field")
        
        # Map type to class
        type_map = {
            "shadowsocks": ShadowsocksOutbound,
            "vmess": VmessOutbound,
            "vless": VlessOutbound,
            "trojan": TrojanOutbound,
            "wireguard": WireguardOutbound,
            "hysteria": HysteriaOutbound,
            "tuic": TuicOutbound,
            "http": HttpOutbound,
            "socks": SocksOutbound,
            "direct": DirectOutbound,
            "block": BlockOutbound,
            "dns": DnsOutbound
        }
        
        if outbound_type not in type_map:
            raise ValueError(f"Unsupported outbound type: {outbound_type}")
        
        outbound_class = type_map[outbound_type]
        return outbound_class(**config)
        
    except Exception as e:
        raise ValueError(f"Invalid outbound configuration: {e}")

def generate_outbound_schema() -> Dict[str, Any]:
    """Generate JSON schema for outbound configuration.
    
    Returns:
        JSON schema dictionary for OutboundModel
    """
    return OutboundConfig.model_json_schema()

def convert_protocol_to_outbound(protocol_config: ProtocolConfig, tag: Optional[str] = None) -> OutboundModel:
    """Convert protocol configuration to outbound format.
    
    Args:
        protocol_config: Protocol configuration
        tag: Optional tag for the outbound
        
    Returns:
        Outbound configuration in sing-box format
    """
    if isinstance(protocol_config, ShadowsocksConfig):
        return ShadowsocksOutbound(
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            method=protocol_config.method,
            password=protocol_config.password,
            plugin=protocol_config.plugin,
            plugin_opts=protocol_config.plugin_opts
        )
    elif isinstance(protocol_config, VmessConfig):
        # Extract first user for outbound
        user = protocol_config.settings.clients[0] if protocol_config.settings.clients else None
        if not user:
            raise ValueError("VMess configuration must have at least one user")
        
        return VmessOutbound(
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            uuid=user.id,
            security=user.security,
            tls=protocol_config.streamSettings.tls_settings if protocol_config.streamSettings else None,
            multiplex=protocol_config.multiplex
        )
    elif isinstance(protocol_config, VlessConfig):
        # Extract first user for outbound
        user = protocol_config.settings.clients[0] if protocol_config.settings.clients else None
        if not user:
            raise ValueError("VLESS configuration must have at least one user")
        
        return VlessOutbound(
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            uuid=user.id,
            flow=user.flow,
            tls=protocol_config.streamSettings.tls_settings if protocol_config.streamSettings else None,
            multiplex=protocol_config.multiplex
        )
    elif isinstance(protocol_config, TrojanConfig):
        return TrojanOutbound(
            tag=tag,
            server=protocol_config.server,
            server_port=protocol_config.server_port,
            password=protocol_config.password,
            tls=protocol_config.tls,
            multiplex=protocol_config.multiplex,
            fallback=protocol_config.fallback
        )
    elif isinstance(protocol_config, WireGuardConfig):
        # Extract first peer for outbound
        peer = protocol_config.peers[0] if protocol_config.peers else None
        if not peer:
            raise ValueError("WireGuard configuration must have at least one peer")
        
        return WireguardOutbound(
            tag=tag,
            server=peer.endpoint.split(':')[0] if peer.endpoint else None,
            server_port=int(peer.endpoint.split(':')[1]) if peer.endpoint and ':' in peer.endpoint else None,
            private_key=protocol_config.interface.private_key,
            peer_public_key=peer.public_key,
            mtu=protocol_config.interface.mtu,
            keepalive=peer.persistent_keepalive is not None
        )
    else:
        raise ValueError(f"Unsupported protocol type: {type(protocol_config)}")

def create_outbound_from_dict(config: Dict[str, Any], tag: Optional[str] = None) -> OutboundModel:
    """Create outbound configuration from dictionary.
    
    Args:
        config: Configuration dictionary
        tag: Optional tag for the outbound
        
    Returns:
        Outbound configuration
    """
    if tag:
        config = {**config, "tag": tag}
    return validate_outbound_config(config) 