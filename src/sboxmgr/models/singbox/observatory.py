"""Observatory models for sing-box configuration."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ObservatoryConfig(BaseModel):
    """Observatory configuration for probing servers."""

    probe_url: Optional[str] = Field(
        default=None,
        description="URL for probing servers, e.g., 'http://www.google.com/generate_204'.",
    )
    probe_interval: Optional[str] = Field(
        default=None, description="Interval for probing, e.g., '1h'."
    )
    subject_selector: Optional[List[str]] = Field(
        default=None, description="Outbound tags to probe."
    )

    model_config = {"extra": "forbid"}
