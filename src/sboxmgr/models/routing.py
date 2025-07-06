"""Routing models for SBoxMgr."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class RouteRule(BaseModel):
    """Routing rule for traffic management."""

    type: Optional[str] = Field(
        default=None, description="Rule type, e.g., 'default', 'logical'."
    )
    inbound: Optional[List[str]] = Field(
        default=None, description="List of inbound tags to match."
    )
    ip_version: Optional[Literal[4, 6]] = Field(
        default=None, description="IP version to match (4 or 6)."
    )
    network: Optional[str] = Field(
        default=None, description="Network type to match, e.g., 'tcp', 'udp'."
    )
    protocol: Optional[Union[str, List[str]]] = Field(
        default=None, description="Protocols to match, e.g., 'dns' or ['http', 'tls']."
    )
    domain: Optional[List[str]] = Field(
        default=None, description="Exact domain names to match."
    )
    domain_suffix: Optional[List[str]] = Field(
        default=None, description="Domain suffixes to match."
    )
    domain_keyword: Optional[List[str]] = Field(
        default=None, description="Domain keywords to match."
    )
    domain_regex: Optional[List[str]] = Field(
        default=None, description="Domain regex patterns to match."
    )
    geosite: Optional[List[str]] = Field(
        default=None, description="Geosite categories to match."
    )
    source_geoip: Optional[List[str]] = Field(
        default=None, description="Source GeoIP codes to match."
    )
    source_ip_cidr: Optional[List[str]] = Field(
        default=None, description="Source IP CIDR ranges to match."
    )
    source_port: Optional[List[int]] = Field(
        default=None, description="Source ports to match."
    )
    source_port_range: Optional[List[str]] = Field(
        default=None, description="Source port ranges to match, e.g., ['80:90']."
    )
    port: Optional[List[int]] = Field(
        default=None, description="Destination ports to match."
    )
    port_range: Optional[List[str]] = Field(
        default=None, description="Destination port ranges to match."
    )
    process_name: Optional[List[str]] = Field(
        default=None, description="Process names to match."
    )
    user: Optional[List[str]] = Field(default=None, description="Usernames to match.")
    invert: Optional[bool] = Field(
        default=None, description="Invert rule matching logic."
    )
    outbound: Optional[str] = Field(default=None, description="Target outbound tag.")

    model_config = {"extra": "forbid"}


class RouteConfig(BaseModel):
    """Routing configuration."""

    rules: Optional[List[RouteRule]] = Field(
        default=None, description="List of routing rules."
    )
    final: Optional[str] = Field(default=None, description="Default outbound tag.")
    auto_detect_interface: Optional[bool] = Field(
        default=None, description="Auto-detect network interface."
    )
    default_interface: Optional[str] = Field(
        default=None, description="Default network interface."
    )
    default_mark: Optional[int] = Field(
        default=None, ge=0, description="Default routing mark."
    )
    geoip: Optional[Dict[str, Any]] = Field(
        default=None, description="GeoIP database settings."
    )
    geosite: Optional[Dict[str, Any]] = Field(
        default=None, description="Geosite database settings."
    )

    model_config = {"extra": "forbid"}
