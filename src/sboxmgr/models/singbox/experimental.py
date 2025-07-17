"""Experimental models for sing-box configuration."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ClashApiConfig(BaseModel):
    """Clash API configuration."""

    external_controller: Optional[str] = Field(
        default=None,
        description="Address for external controller, e.g., '127.0.0.1:9090'.",
    )
    external_ui: Optional[str] = Field(
        default=None, description="Path to external UI directory."
    )
    secret: Optional[str] = Field(
        default=None, description="Secret for API authentication."
    )
    default_mode: Optional[str] = Field(
        default=None, description="Default proxy mode, e.g., 'rule'."
    )

    model_config = {"extra": "forbid"}


class V2RayApiConfig(BaseModel):
    """V2Ray API configuration."""

    listen: Optional[str] = Field(
        default=None, description="Listen address for API, e.g., '127.0.0.1:10085'."
    )
    stats_enabled: Optional[bool] = Field(
        default=None, description="Enable statistics collection."
    )
    stats_outbound_downlink: Optional[bool] = Field(
        default=None, description="Enable outbound downlink stats."
    )
    stats_outbound_uplink: Optional[bool] = Field(
        default=None, description="Enable outbound uplink stats."
    )

    model_config = {"extra": "forbid"}


class CacheFileConfig(BaseModel):
    """Cache file configuration."""

    enabled: Optional[bool] = Field(default=None, description="Enable cache file.")
    path: Optional[str] = Field(default=None, description="Path to cache file.")
    cache_id: Optional[str] = Field(default=None, description="Cache identifier.")
    store_fakeip: Optional[bool] = Field(
        default=None, description="Store fake IP mappings."
    )

    model_config = {"extra": "forbid"}


class ExperimentalConfig(BaseModel):
    """Experimental features configuration."""

    clash_api: Optional[ClashApiConfig] = Field(
        default=None, description="Clash API settings."
    )
    v2ray_api: Optional[V2RayApiConfig] = Field(
        default=None, description="V2Ray API settings."
    )
    cache_file: Optional[CacheFileConfig] = Field(
        default=None, description="Cache file settings."
    )
    geoip: Optional[dict[str, Any]] = Field(
        default=None, description="GeoIP database settings."
    )
    geosite: Optional[dict[str, Any]] = Field(
        default=None, description="Geosite database settings."
    )
    v2ray: Optional[dict[str, Any]] = Field(
        default=None, description="V2Ray-specific experimental settings."
    )

    model_config = {"extra": "forbid"}
