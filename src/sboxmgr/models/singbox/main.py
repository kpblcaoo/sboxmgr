"""Main sing-box configuration model.

This module provides the main SingBoxConfig class that combines all
sing-box configuration components into a single validated model.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .enums import LogLevel
from .dns import DnsConfig
from .ntp import NtpConfig
from .inbounds import Inbound
from .outbounds import Outbound
from .routing import RouteConfig
from .experimental import ExperimentalConfig
from .observatory import ObservatoryConfig


class LogConfig(BaseModel):
    """Logging configuration for sing-box."""

    disabled: Optional[bool] = Field(default=None, description="Disable logging.")
    level: Optional[LogLevel] = Field(default=None, description="Log level.")
    timestamp: Optional[bool] = Field(default=None, description="Include timestamp in log messages.")
    output: Optional[str] = Field(default=None, description="Log output path.")

    model_config = {"extra": "forbid"}


class SingBoxConfig(BaseModel):
    """Complete sing-box configuration model.
    
    This model represents the full sing-box configuration with all supported
    protocols and features. It is validated against sing-box 1.11.13.
    
    Features:
    - 17 inbound protocols (mixed, socks, http, shadowsocks, vmess, vless, 
      trojan, hysteria2, wireguard, tuic, shadowtls, direct, anytls, naive, 
      redirect, tproxy, tun)
    - 18 outbound protocols (shadowsocks, vmess, vless, trojan, hysteria2, 
      wireguard, http, socks, tuic, shadowtls, dns, direct, block, selector, 
      urltest, hysteria, anytls, ssh, tor)
    - Complete DNS, routing, and experimental features support
    """

    log: Optional[LogConfig] = Field(default=None, description="Logging configuration.")
    dns: Optional[DnsConfig] = Field(default=None, description="DNS configuration.")
    ntp: Optional[NtpConfig] = Field(default=None, description="NTP configuration for time synchronization.")
    inbounds: Optional[List[Inbound]] = Field(default=None, description="List of inbound configurations.")
    outbounds: Optional[List[Outbound]] = Field(default=None, description="List of outbound configurations.")
    route: Optional[RouteConfig] = Field(default=None, description="Routing configuration.")
    experimental: Optional[ExperimentalConfig] = Field(default=None, description="Experimental features configuration.")
    observatory: Optional[ObservatoryConfig] = Field(default=None, description="Server probing configuration.")

    model_config = {"extra": "forbid"}

    @field_validator("outbounds")
    def check_outbounds(cls, v):
        """Validate outbounds configuration."""
        if v:
            # Check unique tags
            tags = [o.tag for o in v if o.tag]
            if len(tags) != len(set(tags)):
                raise ValueError("Duplicate outbound tags found")
            
            # Check unique server/port combinations
            servers = [(o.server, o.server_port) for o in v if o.server and o.server_port]
            if len(servers) != len(set(servers)):
                raise ValueError("Duplicate server/port found")
        return v

    @field_validator("inbounds")
    def check_inbounds(cls, v):
        """Validate inbounds configuration."""
        if v:
            # Check unique tags
            tags = [i.tag for i in v if i.tag]
            if len(tags) != len(set(tags)):
                raise ValueError("Duplicate inbound tags found")
            
            # Check unique listen ports
            ports = [i.listen_port for i in v if i.listen_port]
            if len(ports) != len(set(ports)):
                raise ValueError("Duplicate listen ports found")
        return v

    @classmethod
    def generate_schema(cls) -> dict:
        """Generate JSON Schema for sing-box configuration."""
        return cls.model_json_schema()
    
    def to_json(self, **kwargs) -> str:
        """Convert configuration to JSON string."""
        return self.model_dump_json(**kwargs)
    
    def to_dict(self, **kwargs) -> dict:
        """Convert configuration to dictionary."""
        return self.model_dump(**kwargs)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create configuration from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """Create configuration from JSON string."""
        return cls.model_validate_json(json_str)
