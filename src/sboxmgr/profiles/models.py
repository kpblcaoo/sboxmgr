"""Pydantic models for Full Profile Architecture (ADR-0017).

This module defines the core models for profile-based configuration,
including subscriptions, filters, routing, export settings, agent config, and UI preferences.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExportFormat(str, Enum):
    """Supported export formats."""

    SINGBOX = "sing-box"
    CLASH = "clash"
    JSON = "json"


class UIMode(str, Enum):
    """Supported UI modes."""

    CLI = "cli"
    TUI = "tui"
    GUI = "gui"


class SubscriptionProfile(BaseModel):
    """Profile configuration for subscriptions."""

    id: str = Field(..., description="Unique subscription identifier")
    enabled: bool = Field(default=True, description="Whether subscription is enabled")
    priority: int = Field(
        default=1, description="Priority for ordering (lower = higher priority)"
    )

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority field.

        Args:
            v: Priority value to validate.

        Returns:
            Validated priority value.

        Raises:
            ValueError: If priority is less than 1.

        """
        if v < 1:
            raise ValueError("Priority must be >= 1")
        return v


class FilterProfile(BaseModel):
    """Profile configuration for filtering and exclusions."""

    exclude_tags: List[str] = Field(default_factory=list, description="Tags to exclude")
    only_tags: List[str] = Field(
        default_factory=list, description="Only include servers with these tags"
    )
    exclusions: List[str] = Field(
        default_factory=list, description="Server names/IPs to exclude"
    )
    only_enabled: bool = Field(
        default=True, description="Only include enabled subscriptions"
    )


class RoutingProfile(BaseModel):
    """Profile configuration for routing rules."""

    by_source: Dict[str, str] = Field(
        default_factory=dict, description="Route by subscription source ID"
    )
    default_route: str = Field(default="tunnel", description="Default routing mode")
    custom_routes: Dict[str, str] = Field(
        default_factory=dict, description="Custom routing rules"
    )


class ExportProfile(BaseModel):
    """Profile configuration for export settings."""

    format: ExportFormat = Field(
        default=ExportFormat.SINGBOX, description="Export format"
    )
    outbound_profile: str = Field(
        default="vless-real", description="Outbound profile name"
    )
    inbound_profile: str = Field(default="tun", description="Inbound profile name")
    output_file: str = Field(default="config.json", description="Output file path")
    template: Optional[str] = Field(None, description="Custom template path")


class AgentProfile(BaseModel):
    """Profile configuration for agent settings."""

    auto_restart: bool = Field(default=False, description="Auto-restart on failure")
    monitor_latency: bool = Field(default=True, description="Monitor server latency")
    health_check_interval: str = Field(
        default="30s", description="Health check interval"
    )
    log_level: str = Field(default="info", description="Logging level")


class UIProfile(BaseModel):
    """Profile configuration for UI preferences."""

    default_language: str = Field(default="en", description="Default language")
    mode: UIMode = Field(default=UIMode.CLI, description="UI mode")
    theme: Optional[str] = Field(None, description="UI theme")
    show_debug_info: bool = Field(default=False, description="Show debug information")


class FullProfile(BaseModel):
    """Complete profile configuration (ADR-0017)."""

    id: str = Field(..., description="Unique profile identifier")
    description: Optional[str] = Field(None, description="Profile description")

    # Core components
    subscriptions: List[SubscriptionProfile] = Field(
        default_factory=list, description="Subscription configurations"
    )
    filters: FilterProfile = Field(
        default_factory=FilterProfile, description="Filtering and exclusion rules"
    )
    routing: RoutingProfile = Field(
        default_factory=RoutingProfile, description="Routing configuration"
    )
    export: ExportProfile = Field(
        default_factory=ExportProfile, description="Export settings"
    )

    # Optional components
    agent: Optional[AgentProfile] = Field(None, description="Agent configuration")
    ui: Optional[UIProfile] = Field(None, description="UI preferences")

    # Metadata
    version: str = Field(default="1.0", description="Profile version")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    # Extensions
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """Validate profile ID field.

        Args:
            v: Profile ID value to validate.

        Returns:
            Validated and stripped profile ID.

        Raises:
            ValueError: If profile ID is empty or whitespace only.

        """
        if not v or not v.strip():
            raise ValueError("Profile ID cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",  # Reject unknown fields
    )


# Convenience models for backward compatibility
class LegacyProfile(BaseModel):
    """Legacy profile format for migration."""

    subscriptions: List[str] = Field(
        default_factory=list, description="List of subscription URLs"
    )
    exclusions: List[str] = Field(
        default_factory=list, description="List of exclusions"
    )
    export_format: str = Field(default="sing-box", description="Export format")

    model_config = ConfigDict(extra="allow")  # Allow unknown fields for migration


# Type aliases for convenience
Profile = FullProfile
SubscriptionConfig = SubscriptionProfile
FilterConfig = FilterProfile
RoutingConfig = RoutingProfile
ExportConfig = ExportProfile
AgentConfig = AgentProfile
UIConfig = UIProfile
