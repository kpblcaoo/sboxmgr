"""Pydantic schemas for sing-box configuration validation.

This module defines the core data structures for validating sing-box configurations
without requiring external sing-box binary.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class Outbound(BaseModel):
    """Sing-box outbound configuration."""
    
    type: str = Field(..., description="Outbound type (e.g., 'direct', 'urltest', 'vless')")
    tag: str = Field(..., description="Unique outbound tag")
    outbounds: Optional[List[str]] = Field(None, description="List of outbound tags for selectors")
    
    # Common fields for proxy outbounds
    server: Optional[str] = Field(None, description="Server address")
    server_port: Optional[int] = Field(None, description="Server port")
    
    # Allow additional fields for different outbound types
    model_config = {"extra": "allow"}


class RouteRule(BaseModel):
    """Sing-box route rule configuration."""
    
    # Rule matching fields
    inbound: Optional[List[str]] = None
    ip_version: Optional[int] = None
    network: Optional[List[str]] = None
    domain: Optional[List[str]] = None
    domain_suffix: Optional[List[str]] = None
    domain_keyword: Optional[List[str]] = None
    domain_regex: Optional[List[str]] = None
    geosite: Optional[List[str]] = None
    source_geoip: Optional[List[str]] = None
    geoip: Optional[List[str]] = None
    source_ip_cidr: Optional[List[str]] = None
    ip_cidr: Optional[Union[List[str], str]] = None
    source_port: Optional[List[int]] = None
    source_port_range: Optional[List[str]] = None
    port: Optional[List[int]] = None
    port_range: Optional[List[str]] = None
    process_name: Optional[List[str]] = None
    process_path: Optional[List[str]] = None
    package_name: Optional[List[str]] = None
    user: Optional[List[str]] = None
    user_id: Optional[List[int]] = None
    clash_mode: Optional[str] = None
    wifi_ssid: Optional[List[str]] = None
    wifi_bssid: Optional[List[str]] = None
    rule_set: Optional[Union[List[str], str]] = None
    invert: Optional[bool] = None
    
    # Action fields
    outbound: Optional[str] = Field(None, description="Target outbound tag")
    
    # Allow additional fields
    model_config = {"extra": "allow"}


class Route(BaseModel):
    """Sing-box route configuration."""
    
    rules: List[RouteRule] = Field(default_factory=list, description="Route rules")
    final: Optional[str] = Field(None, description="Final outbound tag")
    auto_detect_interface: Optional[bool] = None
    override_android_vpn: Optional[bool] = None
    default_interface: Optional[str] = None
    default_mark: Optional[int] = None
    
    # Allow additional fields
    model_config = {"extra": "allow"}


class Inbound(BaseModel):
    """Sing-box inbound configuration."""
    
    type: str = Field(..., description="Inbound type")
    tag: Optional[str] = Field(None, description="Inbound tag")
    listen: Optional[str] = Field(None, description="Listen address")
    listen_port: Optional[int] = Field(None, description="Listen port")
    
    # Allow additional fields for different inbound types
    model_config = {"extra": "allow"}


class SingBoxConfig(BaseModel):
    """Complete sing-box configuration schema.
    
    This model validates the core structure of sing-box configurations
    without requiring the sing-box binary to be present.
    
    Args:
        log: Logging configuration
        dns: DNS configuration  
        inbounds: List of inbound configurations
        outbounds: List of outbound configurations
        route: Routing configuration
        experimental: Experimental features
    
    Example:
        >>> config_dict = {"outbounds": [{"type": "direct", "tag": "direct"}]}
        >>> config = SingBoxConfig(**config_dict)
        >>> config.outbounds[0].type
        'direct'
    """
    
    log: Optional[Dict[str, Any]] = Field(None, description="Logging configuration")
    dns: Optional[Dict[str, Any]] = Field(None, description="DNS configuration")
    inbounds: Optional[List[Inbound]] = Field(default_factory=list, description="Inbound configurations")
    outbounds: List[Outbound] = Field(..., description="Outbound configurations")
    route: Optional[Route] = Field(None, description="Route configuration")
    experimental: Optional[Dict[str, Any]] = Field(None, description="Experimental features")
    
    # Allow additional fields for extensibility
    model_config = {"extra": "allow"}
    
    @field_validator('outbounds')
    @classmethod
    def validate_outbounds_not_empty(cls, v):
        """Ensure at least one outbound is configured."""
        if not v:
            raise ValueError("At least one outbound must be configured")
        return v
    
    @field_validator('outbounds')
    @classmethod
    def validate_outbound_tags_unique(cls, v):
        """Ensure outbound tags are unique."""
        tags = [outbound.tag for outbound in v if outbound.tag]
        if len(tags) != len(set(tags)):
            raise ValueError("Outbound tags must be unique")
        return v 