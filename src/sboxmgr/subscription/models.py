"""Data models for subscription processing pipeline.

This module defines the core data models used throughout the subscription
processing pipeline including SubscriptionSource, ParsedServer, ClientProfile,
PipelineContext, and other data structures that represent subscription
configuration and processing state.
"""

import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubscriptionSource(BaseModel):
    """Configuration for a subscription data source.

    Defines the source of subscription data including URL, type, headers,
    and other metadata needed to fetch and process the subscription.

    Attributes:
        url: The URL or path to the subscription data.
        source_type: Type of source (url_base64, url_json, file_json, uri_list, etc.).
        headers: Optional HTTP headers for requests.
        label: Optional human-readable label for the source.
        user_agent: Optional custom User-Agent string.

    """

    model_config = ConfigDict(extra="forbid")

    url: str
    source_type: str  # url_base64, url_json, file_json, uri_list, ...
    headers: Optional[dict[str, str]] = None
    label: Optional[str] = None
    user_agent: Optional[str] = None


class ParsedServer(BaseModel):
    """Universal server model for subscription pipeline processing.

    This class represents a parsed server configuration that can handle
    multiple proxy protocols including vmess, vless, trojan, shadowsocks,
    wireguard, hysteria2, tuic, and others.

    Attributes:
        type: Protocol type (vmess, vless, trojan, ss, wireguard, hysteria2, etc.).
        address: Server address (hostname or IP).
        port: Server port number.
        security: Optional security/encryption type.
        meta: Additional protocol-specific parameters.
        uuid: User UUID for vmess, tuic, etc.
        password: Password for trojan, hysteria2, tuic, shadowtls, ssh, etc.
        private_key: Private key for wireguard, ssh.
        peer_public_key: Peer public key for wireguard.
        pre_shared_key: Pre-shared key for wireguard.
        local_address: Local addresses for wireguard.
        username: Username for ssh.
        version: Protocol version for shadowtls.
        uuid_list: List of UUIDs for tuic.
        alpn: ALPN protocols for hysteria2, tuic.
        obfs: Obfuscation settings for hysteria2.
        tls: TLS options for hysteria2, tuic, shadowtls, anytls, ssh.
        handshake: Handshake options for shadowtls.
        congestion_control: Congestion control algorithm for tuic.
        tag: Server tag/label.

    """

    model_config = ConfigDict(
        extra="allow"
    )  # Allow extra fields for protocol-specific params

    type: str
    address: str
    port: int
    security: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
    # Новые поля для поддержки всех протоколов
    uuid: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    peer_public_key: Optional[str] = None
    pre_shared_key: Optional[str] = None
    local_address: Optional[list[str]] = None
    username: Optional[str] = None
    version: Optional[int] = None
    uuid_list: Optional[list[str]] = None
    alpn: Optional[list[str]] = None
    obfs: Optional[dict[str, Any]] = None
    tls: Optional[dict[str, Any]] = None
    handshake: Optional[dict[str, Any]] = None
    congestion_control: Optional[str] = None
    tag: Optional[str] = None


class PipelineContext(BaseModel):
    """Execution context for subscription processing pipeline.

    Contains configuration and state information that flows through
    the entire pipeline execution, including tracing, filtering,
    and debug information.

    Attributes:
        trace_id: Unique identifier for this pipeline execution.
        source: Optional source identifier.
        mode: Pipeline mode ('strict' for fail-fast, 'tolerant' for partial success).
        user_routes: List of user-specified routes for filtering.
        exclusions: List of routes to exclude from processing.
        debug_level: Debug verbosity level.
        metadata: Additional metadata dictionary.
        skip_policies: Whether to skip policy evaluation (for testing).

    """

    model_config = ConfigDict(extra="allow")

    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Optional[str] = None
    mode: str = "tolerant"  # 'strict' or 'tolerant'
    user_routes: list[Any] = Field(default_factory=list)
    exclusions: list[Any] = Field(default_factory=list)
    debug_level: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    skip_policies: bool = False  # Whether to skip policy evaluation (for testing)


class PipelineResult(BaseModel):
    """Result of subscription pipeline execution.

    Contains the output of the pipeline processing including the final
    configuration, execution context, any errors encountered, and
    success status.

    Attributes:
        config: Pipeline output (JSON config, server list, etc.).
        context: Pipeline execution context.
        errors: List of errors encountered during processing.
        success: Whether the pipeline executed successfully.

    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    config: Any  # результат экспорта (например, JSON-конфиг)
    context: PipelineContext
    errors: list
    success: bool


class InboundProfile(BaseModel):
    """Configuration profile for inbound proxy interfaces.

    Defines parameters for incoming proxy connections including type,
    bind address, port, and protocol-specific options. Includes security
    validations to ensure safe defaults.

    Security features:
    - Defaults to localhost binding (127.0.0.1)
    - Uses safe non-standard port defaults
    - Validates port ranges and bind addresses
    - Requires explicit confirmation for external binding

    Attributes:
        type: Inbound type (socks, http, tun, tproxy, ssh, dns, etc.).
        listen: Bind address (defaults to 127.0.0.1 for security).
        port: Port number (defaults to safe values per type).
        options: Additional protocol-specific options.

    """

    type: Literal[
        "socks", "http", "tun", "tproxy", "ssh", "dns", "reality-inbound", "shadowtls"
    ]
    listen: str = Field(
        default="127.0.0.1", description="Адрес для bind, по умолчанию localhost."
    )
    port: Optional[int] = Field(
        default=None, description="Порт, по умолчанию безопасный для типа."
    )
    options: Optional[dict] = Field(
        default_factory=dict, description="Дополнительные параметры."
    )

    @field_validator("listen")
    def validate_listen(cls, v, info):
        """Validate bind address for security.

        Args:
            v: The bind address to validate.
            info: Validation info containing field data.

        Returns:
            The validated bind address.

        Raises:
            ValueError: If bind address is not localhost or private network.

        """
        # Allow 0.0.0.0 only for tproxy and tun that need to listen on all interfaces
        inbound_type = info.data.get("type") if info.data else None
        if inbound_type in ["tproxy", "tun"] and v == "0.0.0.0":
            return v

        if v not in ("127.0.0.1", "::1") and not v.startswith("192.168."):
            raise ValueError(
                "Bind address must be localhost or private network unless explicitly allowed."
            )
        return v

    @field_validator("port")
    def validate_port(cls, v):
        """Validate port number range.

        Args:
            v: The port number to validate.

        Returns:
            The validated port number.

        Raises:
            ValueError: If port is not in valid range.

        """
        if v is None:
            return v
        if not (1024 <= v <= 65535):
            raise ValueError("Port must be in 1024-65535 range.")
        return v


class ClientProfile(BaseModel):
    """Client configuration profile for export operations.

    Defines the client-side configuration including inbound interfaces,
    DNS settings, routing overrides, outbound exclusions, and additional
    options for generating proxy client configurations.

    Attributes:
        inbounds: List of inbound interface configurations.
        dns_mode: DNS resolution mode (system, tunnel, off).
        routing: Optional routing configuration overrides.
        exclude_outbounds: List of outbound types to exclude from export.
        extra: Additional profile parameters.

    """

    inbounds: list[InboundProfile] = Field(
        default_factory=list, description="List of inbound configurations."
    )
    dns_mode: Optional[str] = Field(
        default="system", description="DNS resolution mode."
    )
    routing: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Routing configuration overrides."
    )
    exclude_outbounds: Optional[list[str]] = Field(
        default_factory=list, description="List of outbound types to exclude."
    )
    extra: Optional[dict] = Field(
        default_factory=dict, description="Additional profile parameters."
    )
