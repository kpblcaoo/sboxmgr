"""
DEPRECATED: Configuration models for sing-box.

This module is deprecated and will be removed in a future version.
Use src.sboxmgr.models.singbox instead for the complete sing-box schema.

This file contains legacy models that are being replaced by the modular
sing-box models in src/sboxmgr/models/singbox/.
"""

import warnings

warnings.warn(
    "src.sboxmgr.models.config is deprecated. Use src.sboxmgr.models.singbox instead.",
    DeprecationWarning,
    stacklevel=2
)

"""Configuration models for sing-box."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union, Dict, Any
from .singbox.enums import LogLevel, DomainStrategy
from .singbox.dns import DnsConfig
from .singbox.ntp import NtpConfig
from .singbox.auth import AuthenticationConfig
from .singbox.inbounds import Inbound
from .singbox.outbounds import Outbound
from .singbox.routing import RouteConfig
from .singbox.experimental import ExperimentalConfig
from .singbox.observatory import ObservatoryConfig


class LogConfig(BaseModel):
    """Logging configuration for sing-box."""
    level: Optional[LogLevel] = Field(default=None, description="Log level.")
    timestamp: Optional[bool] = Field(default=None, description="Include timestamp in log messages.")
    output: Optional[str] = Field(default=None, description="Log output path.")
    format: Optional[str] = Field(default=None, description="Log format.")

    model_config = {"extra": "forbid"}


class DnsServer(BaseModel):
    """DNS server configuration."""
    tag: Optional[str] = None
    address: str
    address_resolver: Optional[str] = None
    address_strategy: Optional[DomainStrategy] = None
    strategy: Optional[DomainStrategy] = None
    detours: Optional[List[str]] = None
    client_ip: Optional[str] = None


class DnsRule(BaseModel):
    """DNS rule configuration."""
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
    """DNS configuration."""
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
        """Normalize hosts configuration."""
        if v:
            return {k: v if isinstance(v, list) else [v] for k, v in v.items()}
        return v


class NtpConfig(BaseModel):
    """NTP configuration."""
    enabled: Optional[bool] = None
    server: str
    server_port: Optional[int] = Field(None, ge=1, le=65535)
    interval: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=0)


class CertificateConfig(BaseModel):
    """Certificate configuration."""
    store: Optional[Dict[str, Any]] = None


class ClashApiConfig(BaseModel):
    """Clash API configuration."""
    external_controller: Optional[str] = None
    external_ui: Optional[str] = None
    secret: Optional[str] = None
    default_mode: Optional[str] = None


class V2RayApiConfig(BaseModel):
    """V2Ray API configuration."""
    listen: Optional[str] = None
    stats_enabled: Optional[bool] = None
    stats_outbound_downlink: Optional[bool] = None
    stats_outbound_uplink: Optional[bool] = None


class ExperimentalConfig(BaseModel):
    """Experimental features configuration."""
    clash_api: Optional[ClashApiConfig] = None
    v2ray_api: Optional[V2RayApiConfig] = None
    cache_file: Optional[Dict[str, Any]] = None
    geoip: Optional[Dict[str, Any]] = None
    geosite: Optional[Dict[str, Any]] = None


class SingBoxConfig(BaseModel):
    """Full sing-box configuration (1.11.14)."""
    log: Optional[LogConfig] = Field(default=None, description="Logging configuration.")
    dns: Optional[DnsConfig] = Field(default=None, description="DNS configuration.")
    ntp: Optional[NtpConfig] = Field(default=None, description="NTP configuration for time synchronization.")
    authentication: Optional[AuthenticationConfig] = Field(default=None, description="Global authentication settings.")
    inbounds: Optional[List[Inbound]] = Field(default=None, description="List of inbound configurations.")
    outbounds: Optional[List[Outbound]] = Field(default=None, description="List of outbound configurations.")
    route: Optional[RouteConfig] = Field(default=None, description="Routing configuration.")
    experimental: Optional[ExperimentalConfig] = Field(default=None, description="Experimental features configuration.")
    observatory: Optional[ObservatoryConfig] = Field(default=None, description="Server probing configuration.")

    model_config = {"extra": "forbid"}

    @field_validator("outbounds")
    def check_unique_servers(cls, v):
        """Ensure unique server/port combinations in outbounds."""
        if v:
            servers = [(o.server, o.server_port) for o in v if o.server and o.server_port]
            if len(servers) != len(set(servers)):
                raise ValueError("Duplicate server/port found")
        return v

    @field_validator("inbounds")
    def check_unique_listen_ports(cls, v):
        """Ensure unique listen ports in inbounds."""
        if v:
            ports = [i.listen_port for i in v if i.listen_port]
            if len(ports) != len(set(ports)):
                raise ValueError("Duplicate listen ports found")
        return v

    @classmethod
    def generate_schema(cls) -> dict:
        """Generate JSON Schema for sing-box configuration."""
        return cls.model_json_schema() 