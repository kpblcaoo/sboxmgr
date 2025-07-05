"""Common configuration models for VPN protocols.

This module provides shared configuration models used across different VPN protocols
including TLS, stream settings, and multiplexing configurations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from .transport import RealityConfig, UtlsConfig, WsConfig, HttpConfig, GrpcConfig, QuicConfig


class TlsConfig(BaseModel):
    """TLS configuration for protocols with detailed obfuscation models."""

    enabled: Optional[bool] = Field(True, description="Enable TLS for connection")
    server_name: Optional[str] = Field(None, description="SNI for TLS connection")
    alpn: Optional[List[str]] = Field(None, description="ALPN protocols list (e.g., h2, http/1.1)")
    min_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Minimum TLS version")
    max_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(None, description="Maximum TLS version")
    certificate_path: Optional[str] = Field(None, description="Path to certificate file")
    key_path: Optional[str] = Field(None, description="Path to key file")
    certificate: Optional[str] = Field(None, description="Certificate content in PEM format")
    key: Optional[str] = Field(None, description="Key content in PEM format")
    allow_insecure: Optional[bool] = Field(False, description="Allow insecure connections (not recommended)")
    ech: Optional[Dict[str, Any]] = Field(None, description="ECH settings for SNI protection")
    utls: Optional[UtlsConfig] = Field(None, description="uTLS settings for TLS client emulation")
    reality: Optional[RealityConfig] = Field(None, description="Reality settings for SNI protection")

    class Config:
        extra = "forbid"


class StreamSettings(BaseModel):
    """Transport layer settings with detailed configuration models."""

    network: Optional[Literal["tcp", "udp", "ws", "http", "grpc", "quic"]] = Field(None, description="Transport type (TCP, WebSocket, gRPC, etc.)")
    security: Optional[Literal["none", "tls", "reality"]] = Field(None, description="Encryption type (TLS, REALITY or none)")
    tls_settings: Optional[TlsConfig] = Field(None, description="TLS settings for transport")
    ws_settings: Optional[WsConfig] = Field(None, description="WebSocket settings")
    http_settings: Optional[HttpConfig] = Field(None, description="HTTP/2 settings")
    grpc_settings: Optional[GrpcConfig] = Field(None, description="gRPC settings")
    quic_settings: Optional[QuicConfig] = Field(None, description="QUIC settings")

    class Config:
        extra = "forbid"


class MultiplexConfig(BaseModel):
    """Multiplexing configuration."""

    enabled: Optional[bool] = Field(None, description="Enable multiplexing")
    protocol: Optional[Literal["smux", "yamux", "h2mux"]] = Field(None, description="Multiplexing protocol")
    max_connections: Optional[int] = Field(None, ge=1, description="Maximum number of connections")
    min_streams: Optional[int] = Field(None, ge=0, description="Minimum number of streams")
    max_streams: Optional[int] = Field(None, ge=0, description="Maximum number of streams")
    padding: Optional[bool] = Field(None, description="Enable padding for obfuscation")

    class Config:
        extra = "forbid" 