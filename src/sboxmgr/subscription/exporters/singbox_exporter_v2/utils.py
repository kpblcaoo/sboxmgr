"""Utility functions for sing-box exporter v2.

This module provides helper functions for converting TLS and transport configurations
from ParsedServer objects to appropriate sing-box model instances.
"""

from typing import Optional

# Import new sing-box models
from sboxmgr.models.singbox import TlsConfig, TransportConfig

from ...models import ParsedServer


def convert_tls_config(server: ParsedServer) -> Optional[TlsConfig]:
    """Convert server TLS data to TlsConfig."""
    tls_data = {}

    # Add server name (SNI)
    if server.meta.get("servername") or server.meta.get("sni"):
        tls_data["server_name"] = server.meta.get("servername") or server.meta.get(
            "sni"
        )

    # Add ALPN
    if server.meta.get("alpn"):
        if isinstance(server.meta["alpn"], list):
            tls_data["alpn"] = server.meta["alpn"]
        else:
            # If alpn is a string, split by comma
            tls_data["alpn"] = [x.strip() for x in server.meta["alpn"].split(",")]

    # Add insecure flag
    if server.meta.get("insecure") or server.meta.get("allow_insecure"):
        tls_data["insecure"] = server.meta.get("insecure") or server.meta.get(
            "allow_insecure"
        )

    # Add other TLS options
    if server.meta.get("fingerprint"):
        tls_data["utls"] = {"enabled": True, "fingerprint": server.meta["fingerprint"]}

    if server.meta.get("reality"):
        tls_data["reality"] = server.meta["reality"]

    if server.meta.get("ech"):
        tls_data["ech"] = server.meta["ech"]

    return TlsConfig(**tls_data) if tls_data else None


def convert_transport_config(server: ParsedServer) -> Optional[TransportConfig]:
    """Convert server transport data to TransportConfig."""
    transport_data = {}

    network = server.meta.get("network")
    if network in ["ws", "grpc", "http", "httpupgrade", "quic", "tcp", "udp"]:
        transport_data["network"] = network

        if network == "ws":
            if server.meta.get("ws_path"):
                transport_data["ws_opts"] = {"path": server.meta["ws_path"]}
            if server.meta.get("ws_headers"):
                transport_data["ws_opts"] = transport_data.get("ws_opts", {})
                transport_data["ws_opts"]["headers"] = server.meta["ws_headers"]
        elif network == "grpc":
            if server.meta.get("grpc_service_name"):
                transport_data["grpc_opts"] = {
                    "serviceName": server.meta["grpc_service_name"]
                }
        elif network == "http":
            if server.meta.get("http_path"):
                transport_data["http_opts"] = {"path": server.meta["http_path"]}
            if server.meta.get("http_host"):
                transport_data["http_opts"] = transport_data.get("http_opts", {})
                transport_data["http_opts"]["host"] = server.meta["http_host"]

    return TransportConfig(**transport_data) if transport_data else None
