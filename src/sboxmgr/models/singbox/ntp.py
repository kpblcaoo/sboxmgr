"""NTP models for sing-box configuration."""

from pydantic import BaseModel, Field
from typing import Optional

class NtpConfig(BaseModel):
    """NTP configuration for time synchronization."""

    enabled: Optional[bool] = Field(default=None, description="Enable NTP synchronization.")
    server: str = Field(..., description="NTP server address, e.g., 'pool.ntp.org'.")
    server_port: Optional[int] = Field(default=None, ge=1, le=65535, description="NTP server port, typically 123.")
    interval: Optional[str] = Field(default=None, description="Sync interval, e.g., '1h', '30m'.")
    timeout: Optional[int] = Field(default=None, ge=0, description="Timeout for NTP queries in seconds.")
    write_system: Optional[bool] = Field(default=None, description="Allow writing to system clock.")
    set_system: Optional[bool] = Field(default=None, description="Set system clock on startup.")

    model_config = {"extra": "forbid"} 