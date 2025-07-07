"""Transport configuration models for VPN protocols.

This module provides transport-specific configuration models for various protocols
including WebSocket, HTTP/2, gRPC, and QUIC transports.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RealityConfig(BaseModel):
    """Reality protocol configuration for SNI protection."""

    public_key: str = Field(..., description="Reality public key")
    short_id: Optional[str] = Field(None, description="Reality short ID")
    max_time_difference: Optional[int] = Field(
        None, ge=0, description="Maximum time difference in seconds"
    )
    fingerprint: Optional[str] = Field(None, description="Browser fingerprint")

    class Config:
        extra = "forbid"


class UtlsConfig(BaseModel):
    """uTLS configuration for TLS client emulation."""

    enabled: bool = Field(True, description="Enable uTLS")
    fingerprint: Optional[
        Literal[
            "chrome",
            "firefox",
            "safari",
            "ios",
            "android",
            "edge",
            "360",
            "qq",
            "random",
            "randomized",
        ]
    ] = Field(None, description="Browser fingerprint to emulate")

    class Config:
        extra = "forbid"


class WsConfig(BaseModel):
    """WebSocket transport configuration."""

    path: str = Field(..., description="WebSocket path")
    headers: Optional[Dict[str, str]] = Field(None, description="WebSocket headers")
    max_early_data: Optional[int] = Field(
        None, ge=0, description="Maximum early data size"
    )
    use_browser_forwarding: Optional[bool] = Field(
        None, description="Use browser forwarding"
    )

    class Config:
        extra = "forbid"


class HttpConfig(BaseModel):
    """HTTP/2 transport configuration."""

    host: List[str] = Field(..., description="HTTP host list")
    path: str = Field(..., description="HTTP path")

    class Config:
        extra = "forbid"


class GrpcConfig(BaseModel):
    """gRPC transport configuration."""

    service_name: str = Field(..., description="gRPC service name")
    multi_mode: Optional[bool] = Field(None, description="Enable multi mode")
    idle_timeout: Optional[int] = Field(
        None, ge=0, description="Idle timeout in seconds"
    )
    health_check_timeout: Optional[int] = Field(
        None, ge=0, description="Health check timeout in seconds"
    )
    permit_without_stream: Optional[bool] = Field(
        None, description="Permit without stream"
    )
    initial_windows_size: Optional[int] = Field(
        None, ge=0, description="Initial window size"
    )

    class Config:
        extra = "forbid"


class QuicConfig(BaseModel):
    """QUIC transport configuration."""

    security: Literal["none", "tls"] = Field("none", description="QUIC security type")
    key: Optional[str] = Field(None, description="QUIC key")
    certificate: Optional[str] = Field(None, description="QUIC certificate")

    class Config:
        extra = "forbid"
