from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class TlsConfig(BaseModel):
    """TLS configuration for secure connections."""

    enabled: Optional[bool] = Field(default=True, description="Enable TLS for the connection.")
    disable_sni: Optional[bool] = Field(default=False, description="Disable SNI in TLS handshake.")
    server_name: Optional[str] = Field(default=None, description="SNI for TLS connection.")
    insecure: Optional[bool] = Field(default=False, description="Allow insecure connections (not recommended).")
    alpn: Optional[List[str]] = Field(default=None, description="List of ALPN protocols (e.g., h2, http/1.1).")
    min_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(default=None, description="Minimum TLS version.")
    max_version: Optional[Literal["1.0", "1.1", "1.2", "1.3"]] = Field(default=None, description="Maximum TLS version.")
    certificate_path: Optional[str] = Field(default=None, description="Path to TLS certificate file.")
    key_path: Optional[str] = Field(default=None, description="Path to TLS key file.")
    certificate: Optional[str] = Field(default=None, description="Certificate content in PEM format.")
    key: Optional[str] = Field(default=None, description="Key content in PEM format.")
    ech: Optional[Dict[str, Any]] = Field(default=None, description="Encrypted Client Hello settings.")
    utls: Optional[Dict[str, Any]] = Field(default=None, description="uTLS settings for client fingerprinting, e.g., {'fingerprint': 'chrome'}.")

    model_config = {"extra": "forbid"}

class MultiplexConfig(BaseModel):
    """Multiplexing configuration."""

    enabled: Optional[bool] = Field(default=None, description="Enable multiplexing.")
    protocol: Optional[Literal["smux", "yamux"]] = Field(default=None, description="Multiplexing protocol.")
    max_connections: Optional[int] = Field(default=None, ge=1, description="Maximum number of connections.")
    min_streams: Optional[int] = Field(default=None, ge=0, description="Minimum number of streams.")
    max_streams: Optional[int] = Field(default=None, ge=0, description="Maximum number of streams.")
    padding: Optional[bool] = Field(default=None, description="Enable padding for obfuscation.")

    model_config = {"extra": "forbid"}

class TransportConfig(BaseModel):
    """Transport layer settings."""

    network: Optional[Literal["tcp", "udp", "ws", "http", "grpc", "httpupgrade", "quic"]] = Field(default=None, description="Transport protocol.")
    ws_opts: Optional[Dict[str, Any]] = Field(default=None, description="WebSocket settings, e.g., {'path': '/ws', 'headers': {'Host': 'example.com'}}.")
    http_opts: Optional[Dict[str, Any]] = Field(default=None, description="HTTP/2 settings, e.g., {'host': 'example.com', 'path': '/http2'}.")
    grpc_opts: Optional[Dict[str, Any]] = Field(default=None, description="gRPC settings, e.g., {'serviceName': 'proxy'}.")
    httpupgrade_opts: Optional[Dict[str, Any]] = Field(default=None, description="HTTPUpgrade settings.")
    quic_opts: Optional[Dict[str, Any]] = Field(default=None, description="QUIC settings.")

    model_config = {"extra": "forbid"} 