"""Authentication models for sing-box configuration."""

from pydantic import BaseModel, Field
from typing import List, Optional

class AuthenticationUser(BaseModel):
    """User authentication settings."""

    username: str = Field(..., description="Username for authentication.")
    password: str = Field(..., description="Password for authentication.")

    model_config = {"extra": "forbid"}

class AuthenticationConfig(BaseModel):
    """Global authentication configuration."""

    users: List[AuthenticationUser] = Field(..., description="List of users for authentication.")
    set_system_proxy: Optional[bool] = Field(default=None, description="Set as system proxy.")

    model_config = {"extra": "forbid"}
