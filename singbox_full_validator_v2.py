```python
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Literal, Optional, Union, Dict, Any, Annotated
from enum import Enum
import json
from pathlib import Path

# Enums
class LogLevel(str, Enum):
    trace = "trace"
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"
    panic = "panic"

class DomainStrategy(str, Enum):
    prefer_ipv4 = "prefer_ipv4"
    prefer_ipv6 = "prefer_ipv6"
    ipv4_only = "ipv4_only"
    ipv6_only = "ipv6_only"

class Network(str, Enum):
    tcp = "tcp"
    udp = "udp"
    tcp_udp = "tcp,udp"

# Log Configuration
class LogConfig(BaseModel):
    disabled: Optional[bool] = None
    level: Optional[LogLevel] = None
    output: Optional[str] = None
    timestamp: Optional[bool] = None
    timezone: Optional[str] = None
    log_terminal: Optional[bool] = None
    log_file: Optional[str] = None
    log_rotate: Optional[bool] = None
    log_max_size: Optional[int] = Field(None, ge=0)
    log_max_days: Optional[int] = Field(None, ge=0)
    log_compress: Optional[bool] = None

# DNS Configuration
class DnsServer(BaseModel):
    tag: Optional[str] = None
    address: str
    address_resolver: Optional[str] = None
    address_strategy: Optional[DomainStrategy] = None
    strategy: Optional[DomainStrategy] = None
    detours: Optional[List[str]] = None
    client_ip: Optional[str] = None

class DnsRule(BaseModel):
    type: str
    inbound: Optional[List[str]] = None
    ip_version: Optional[Literal[4, 6]] = None
    network: Optional[str] = None
    protocol: Optional[List[str]] = None
    domain: Optional[List[str]] = None
    domain_suffix: Optional[List[str]] = None
    domain_keyword: Optional[List[str]] = None
    domain_regex: Optional[List[str]] = None
    geosite: Optional[List[str]] = None
    source_geoip: Optional[List[str]] = None
    source_ip_cidr: Optional[List[str]] = None
    source_port: Optional[List[int]] = Field(None, ge=0, le=65535)
    source_port_range: Optional[List[str]] = None
    port: Optional[List[int]] = Field(None, ge=0, le=65535)
    port_range: Optional[List[str]] = None
    process_name: Optional[List[str]] = None
    user: Optional[List[str]] = None
    invert: Optional[bool] = None
    outbound: Optional[str] = None
    server: str

class DnsConfig(BaseModel):
    servers: Optional[List[DnsServer]] = None
    rules: Optional[List[DnsRule]] = None
    final: Optional[str] = None
    strategy: Optional[DomainStrategy] = None
    disable_cache: Optional[bool] = None
    disable_expire: Optional[bool] = None
    independent_cache: Optional[bool] = None
    reverse_mapping: Optional[bool] = None
    fakeip: Optional[Dict[str, Any]] = None
    hosts: Optional[Dict[str, Union[str, List[str]]]] = None

    @field_validator("hosts", mode="before")
    def normalize_hosts(cls, v):
        if v:
            return {k: v if isinstance(v, list) else [v] for k, v in v.items()}
        return v

# NTP Configuration
class NtpConfig(BaseModel):
    enabled: Optional[bool] = None
    server: str
    server_port: Optional[int] = Field(None, ge=1, le=65535)
    interval: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=0)

# Certificate Configuration
class CertificateConfig(BaseModel):
    store: Optional[Dict[str, Any]] = None

# TLS Configuration
class TlsConfig(BaseModel):
    enabled: Optional[bool] = None
    server_name: Optional[str] = None
    alpn: Optional[List[str]] = None
    min_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = None
    max_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = None
    certificate_path: Optional[str] = None
    key_path: Optional[str] = None
    certificate: Optional[str] = None
    key: Optional[str] = None
    ech: Optional[Dict[str, Any]] = None
    utls: Optional[Dict[str, Any]] = None

# Multiplex Configuration
class MultiplexConfig(BaseModel):
    enabled: Optional[bool] = None
    protocol: Optional[Literal["smux", "yamux", "h2mux"]] = None
    max_connections: Optional[int] = Field(None, ge=1)
    min_streams: Optional[int] = Field(None, ge=0)
    max_streams: Optional[int] = Field(None, ge=0)
    padding: Optional[bool] = None

# Endpoint Configuration
class EndpointConfig(BaseModel):
    name: str
    address: str

# User Configurations
class SocksUser(BaseModel):
    username: str
    password: str

class HttpUser(BaseModel):
    username: str
    password: str

class VmessUser(BaseModel):
    id: str
    alterId: Optional[int] = Field(0, ge=0)
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = "auto"

class VlessUser(BaseModel):
    id: str
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = None

class TrojanUser(BaseModel):
    password: str

class HysteriaUser(BaseModel):
    password: str

class TuicUser(BaseModel):
    uuid: str
    password: str

# Inbound Configurations
class InboundBase(BaseModel):
    type: str
    tag: Optional[str] = None
    listen: Optional[str] = None
    listen_port: Optional[int] = Field(None, ge=0, le=65535)
    tcp_fast_open: Optional[bool] = None
    udp_fragment: Optional[bool] = None
    sniff: Optional[bool] = None
    domain_strategy: Optional[DomainStrategy] = None

class DirectInbound(InboundBase):
    type: Literal["direct"] = "direct"
    override_address: Optional[str] = None
    override_port: Optional[int] = Field(None, ge=0, le=65535)

class SocksInbound(InboundBase):
    type: Literal["socks"] = "socks"
    users: Optional[List[SocksUser]] = None

class HttpInbound(InboundBase):
    type: Literal["http"] = "http"
    users: Optional[List[HttpUser]] = None
    tls: Optional[TlsConfig] = None

class ShadowsocksInbound(InboundBase):
    type: Literal["shadowsocks"] = "shadowsocks"
    method: str
    password: str
    network: Optional[Network] = None

class VmessInbound(InboundBase):
    type: Literal["vmess"] = "vmess"
    users: Optional[List[VmessUser]] = None
    tls: Optional[TlsConfig] = None

class VlessInbound(InboundBase):
    type: Literal["vless"] = "vless"
    users: Optional[List[VlessUser]] = None
    tls: Optional[TlsConfig] = None

class TrojanInbound(InboundBase):
    type: Literal["trojan"] = "trojan"
    users: Optional[List[TrojanUser]] = None
    tls: Optional[TlsConfig] = None

class HysteriaInbound(InboundBase):
    type: Literal["hysteria"] = "hysteria"
    up_mbps: Optional[int] = Field(None, ge=0)
    down_mbps: Optional[int] = Field(None, ge=0)
    obfs: Optional[str] = None
    users: Optional[List[HysteriaUser]] = None
    tls: Optional[TlsConfig] = None

class WireguardInbound(InboundBase):
    type: Literal["wireguard"] = "wireguard"
    private_key: str
    peer_public_key: str
    mtu: Optional[int] = Field(default=0, ge=0)
    keepalive: Optional[bool] = False
    system_interface: Optional[bool] = None

class TuicInbound(InboundBase):
    type: Literal["tuic"] = "tuic"
    users: Optional[List[TuicUser]] = None
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = None
    tls: Optional[TlsConfig] = None

Inbound = Annotated[
    Union[
        DirectInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
        VmessInbound, VlessInbound, TrojanInbound, HysteriaInbound,
        WireguardInbound, TuicInbound
    ],
    Field(discriminator="type")
]

# Outbound Configurations
class OutboundBase(BaseModel):
    type: str
    tag: Optional[str] = None
    server: Optional[str] = None
    server_port: Optional[int] = Field(None, ge=1, le=65535)
    tls: Optional[TlsConfig] = None
    multiplex: Optional[MultiplexConfig] = None
    local_address: Optional[List[str]] = None

class ShadowsocksOutbound(OutboundBase):
    type: Literal["shadowsocks"] = "shadowsocks"
    method: str
    password: str
    plugin: Optional[str] = None
    plugin_opts: Optional[Dict[str, Any]] = None

class VmessOutbound(OutboundBase):
    type: Literal["vmess"] = "vmess"
    uuid: str
    security: Optional[Literal["auto", "aes-128-gcm", "chacha20-poly1305", "none"]] = "auto"
    packet_encoding: Optional[Literal["packet", "xudp"]] = None

class VlessOutbound(OutboundBase):
    type: Literal["vless"] = "vless"
    uuid: str
    flow: Optional[Literal["xtls-rprx-vision", "xtls-rprx-direct"]] = None
    packet_encoding: Optional[Literal["packet", "xudp"]] = None

class TrojanOutbound(OutboundBase):
    type: Literal["trojan"] = "trojan"
    password: str
    fallback: Optional[Dict[str, Any]] = None

class HysteriaOutbound(OutboundBase):
    type: Literal["hysteria"] = "hysteria"
    up_mbps: Optional[int] = Field(None, ge=0)
    down_mbps: Optional[int] = Field(None, ge=0)
    obfs: Optional[str] = None
    auth_str: Optional[str] = None

class WireguardOutbound(OutboundBase):
    type: Literal["wireguard"] = "wireguard"
    private_key: str
    peer_public_key: str
    mtu: Optional[int] = Field(default=0, ge=0)
    keepalive: Optional[bool] = False
    peers: Optional[List[Dict[str, Any]]] = None
    reserved: Optional[List[int]] = None

class HttpOutbound(OutboundBase):
    type: Literal["http"] = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None

class SocksOutbound(OutboundBase):
    type: Literal["socks"] = "socks"
    version: Optional[Literal["4", "4a", "5"]] = None
    username: Optional[str] = None
    password: Optional[str] = None

class TuicOutbound(OutboundBase):
    type: Literal["tuic"] = "tuic"
    uuid: str
    password: str
    congestion_control: Optional[Literal["bbr", "cubic", "new_reno"]] = None
    zero_rtt_handshake: Optional[bool] = None

class DirectOutbound(OutboundBase):
    type: Literal["direct"] = "direct"
    override_address: Optional[str] = None
    override_port: Optional[int] = Field(None, ge=0, le=65535)

Outbound = Annotated[
    Union[
        ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
        HysteriaOutbound, WireguardOutbound, HttpOutbound, SocksOutbound,
        TuicOutbound, DirectOutbound
    ],
    Field(discriminator="type")
]

# Route Configuration
class RouteRule(BaseModel):
    type: str
    inbound: Optional[List[str]] = None
    ip_version: Optional[Literal[4, 6]] = None
    network: Optional[str] = None
    protocol: Optional[List[str]] = None
    domain: Optional[List[str]] = None
    domain_suffix: Optional[List[str]] = None
    domain_keyword: Optional[List[str]] = None
    domain_regex: Optional[List[str]] = None
    geosite: Optional[List[str]] = None
    source_geoip: Optional[List[str]] = None
    source_ip_cidr: Optional[List[str]] = None
    source_port: Optional[List[int]] = Field(None, ge=0, le=65535)
    source_port_range: Optional[List[str]] = None
    port: Optional[List[int]] = Field(None, ge=0, le=65535)
    port_range: Optional[List[str]] = None
    process_name: Optional[List[str]] = None
    user: Optional[List[str]] = None
    invert: Optional[bool] = None
    outbound: Optional[str] = None

class RouteConfig(BaseModel):
    rules: Optional[List[RouteRule]] = None
    final: Optional[str] = None
    auto_detect_interface: Optional[bool] = None
    default_interface: Optional[str] = None
    default_mark: Optional[int] = Field(None, ge=0)

# Service Configuration
class ServiceConfig(BaseModel):
    type: str
    args: Optional[Dict[str, Any]] = None

# Experimental Configuration
class ClashApiConfig(BaseModel):
    external_controller: Optional[str] = None
    external_ui: Optional[str] = None
    secret: Optional[str] = None
    default_mode: Optional[str] = None

class V2RayApiConfig(BaseModel):
    listen: Optional[str] = None
    stats_enabled: Optional[bool] = None
    stats_outbound_downlink: Optional[bool] = None
    stats_outbound_uplink: Optional[bool] = None

class ExperimentalConfig(BaseModel):
    clash_api: Optional[ClashApiConfig] = None
    v2ray_api: Optional[V2RayApiConfig] = None
    cache_file: Optional[Dict[str, Any]] = None
    geoip: Optional[Dict[str, Any]] = None
    geosite: Optional[Dict[str, Any]] = None

# Главная модель
class SingBoxConfig(BaseModel):
    log: Optional[LogConfig] = None
    dns: Optional[DnsConfig] = None
    ntp: Optional[NtpConfig] = None
    certificate: Optional[CertificateConfig] = None
    endpoints: Optional[List[EndpointConfig]] = None
    inbounds: Optional[List[Inbound]] = None
    outbounds: Optional[List[Outbound]] = None
    route: Optional[RouteConfig] = None
    services: Optional[List[ServiceConfig]] = None
    experimental: Optional[ExperimentalConfig] = None

    class Config:
        extra = "forbid"

    @field_validator("outbounds")
    def check_unique_servers(cls, v):
        if v:
            servers = [(o.server, o.server_port) for o in v if o.server and o.server_port]
            if len(servers) != len(set(servers)):
                raise ValueError("Duplicate server/port found")
        return v

    @field_validator("inbounds")
    def check_unique_listen_ports(cls, v):
        if v:
            ports = [i.listen_port for i in v if i.listen_port]
            if len(ports) != len(set(ports)):
                raise ValueError("Duplicate listen ports found")
        return v

    @classmethod
    def generate_schema(cls) -> dict:
        return cls.model_json_schema()

# Валидатор для CLI
def validate_singbox_config(config_path: Path) -> bool:
    try:
        config_data = json.loads(config_path.read_text())
        SingBoxConfig.parse_obj(config_data)
        print("✅ Configuration validated successfully")
        return True
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"❌ Validation failed: {e}")
        return False

# CLI-команда для генерации схемы
def generate_singbox_schema(output_path: Path) -> None:
    schema = SingBoxConfig.generate_schema()
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"✅ Schema generated: {output_path}")

# Пример использования
if __name__ == "__main__":
    config_path = Path("config.json")
    config_path.write_text(json.dumps({
        "log": {"level": "info", "timestamp": True},
        "outbounds": [
            {
                "type": "wireguard",
                "server": "example.com",
                "server_port": 443,
                "private_key": "abc",
                "peer_public_key": "xyz",
                "mtu": 0,
                "keepalive": False
            },
            {
                "type": "shadowsocks",
                "server": "ss.example.com",
                "server_port": 8388,
                "method": "aes-256-gcm",
                "password": "secret"
            }
        ],
        "inbounds": [
            {
                "type": "socks",
                "listen": "127.0.0.1",
                "listen_port": 1080,
                "users": [{"username": "user", "password": "pass"}]
            }
        ],
        "dns": {
            "servers": [{"address": "8.8.8.8"}],
            "strategy": "prefer_ipv4"
        }
    }))
    validate_singbox_config(config_path)
    generate_singbox_schema(Path("singbox_schema.json"))
```