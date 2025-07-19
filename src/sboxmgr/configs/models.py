"""Configuration models for sboxmgr (ADR-0020).

This module defines the two-layer data model:
- FullProfile: User-friendly configuration model
- ClientConfig: Machine-readable export model
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import TypeAlias


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


class SubscriptionConfig(BaseModel):
    """Config configuration for subscriptions."""

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


class FilterConfig(BaseModel):
    """Config configuration for filtering and exclusions."""

    exclude_tags: list[str] = Field(default_factory=list, description="Tags to exclude")
    only_tags: list[str] = Field(
        default_factory=list, description="Only include servers with these tags"
    )
    exclusions: list[str] = Field(
        default_factory=list, description="Server names/IPs to exclude"
    )
    only_enabled: bool = Field(
        default=True, description="Only include enabled subscriptions"
    )


class RoutingConfig(BaseModel):
    """Config configuration for routing rules."""

    by_source: dict[str, str] = Field(
        default_factory=dict, description="Route by subscription source ID"
    )
    default_route: str = Field(default="tunnel", description="Default routing mode")
    custom_routes: dict[str, str] = Field(
        default_factory=dict, description="Custom routing rules"
    )


class ExportConfig(BaseModel):
    """Config configuration for export settings."""

    format: ExportFormat = Field(
        default=ExportFormat.SINGBOX, description="Export format"
    )
    outbound_profile: str = Field(
        default="vless-real", description="Outbound profile name"
    )
    inbound_profile: str = Field(default="tun", description="Inbound profile name")
    output_file: str = Field(default="config.json", description="Output file path")
    template: Optional[str] = Field(default=None, description="Custom template path")


class AgentConfig(BaseModel):
    """Config configuration for agent settings."""

    auto_restart: bool = Field(default=False, description="Auto-restart on failure")
    monitor_latency: bool = Field(default=True, description="Monitor server latency")
    health_check_interval: str = Field(
        default="30s", description="Health check interval"
    )
    log_level: str = Field(default="info", description="Logging level")


class UIConfig(BaseModel):
    """Config configuration for UI preferences."""

    default_language: str = Field(default="en", description="Default language")
    mode: UIMode = Field(default=UIMode.CLI, description="UI mode")
    theme: Optional[str] = Field(None, description="UI theme")
    show_debug_info: bool = Field(default=False, description="Show debug information")


class FullProfile(BaseModel):
    """Complete user configuration (ADR-0017, ADR-0020).

    FullProfile represents the user's complete configuration - the "source of truth"
    for all user settings. This is what users edit and manage.
    """

    id: str = Field(..., description="Unique profile identifier")
    description: Optional[str] = Field(None, description="Profile description")

    # Core components
    subscriptions: list[SubscriptionConfig] = Field(
        default_factory=list, description="Subscription configurations"
    )
    filters: FilterConfig = Field(
        default_factory=FilterConfig, description="Filtering and exclusion rules"
    )
    routing: RoutingConfig = Field(
        default_factory=RoutingConfig, description="Routing configuration"
    )
    export: ExportConfig = Field(
        default_factory=lambda: ExportConfig(), description="Export settings"
    )

    # Optional components
    agent: Optional[AgentConfig] = Field(None, description="Agent configuration")
    ui: Optional[UIConfig] = Field(None, description="UI preferences")

    # Metadata
    version: str = Field(default="1.0", description="Profile version")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    # Extensions
    metadata: dict[str, Any] = Field(
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


class ClientConfig(BaseModel):
    """Export artifact for backend consumption (ADR-0020).

    ClientConfig represents the machine-readable configuration that is consumed
    by backends like sing-box, Docker containers, or mobile clients.
    """

    # Structure depends on export format (sing-box, clash, etc.)
    # This is a placeholder - actual structure will be defined by exporters
    config: dict[str, Any] = Field(..., description="Backend-specific configuration")
    format: ExportFormat = Field(..., description="Export format")
    version: str = Field(default="1.0", description="Config version")
    generated_at: Optional[str] = Field(None, description="Generation timestamp")

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )


# Convenience models for backward compatibility
class ValidationResult(BaseModel):
    """Result of profile validation.

    Attributes:
        valid: Whether the profile is valid
        errors: List of validation errors
        warnings: List of validation warnings

    """

    valid: bool = Field(..., description="Whether the profile is valid")
    errors: list[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of validation warnings"
    )


class LegacyConfig(BaseModel):
    """Legacy config format for migration."""

    subscriptions: list[str] = Field(
        default_factory=list, description="List of subscription URLs"
    )
    exclusions: list[str] = Field(
        default_factory=list, description="List of exclusions"
    )
    export_format: str = Field(default="sing-box", description="Export format")

    model_config = ConfigDict(extra="allow")  # Allow unknown fields for migration


# Type aliases for convenience and backward compatibility
# Backward compatibility aliases (TODO: remove after v1.0)
UserConfig: TypeAlias = FullProfile  # TODO: remove after v1.0
Config: TypeAlias = FullProfile  # TODO: remove after v1.0
SubscriptionProfile: TypeAlias = SubscriptionConfig  # TODO: remove after v1.0
FilterProfile: TypeAlias = FilterConfig  # TODO: remove after v1.0
RoutingProfile: TypeAlias = RoutingConfig  # TODO: remove after v1.0
ExportProfile: TypeAlias = ExportConfig  # TODO: remove after v1.0
AgentProfile: TypeAlias = AgentConfig  # TODO: remove after v1.0
UIProfile = UIConfig  # Backward compatibility
LegacyProfile = LegacyConfig  # Backward compatibility
