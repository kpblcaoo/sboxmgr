"""Base classes for sing-box models with smart export functionality."""

from typing import Any

from pydantic import BaseModel


class SingBoxModelBase(BaseModel):
    """Base class for sing-box models with smart export functionality."""

    def smart_dump(
        self, exclude_unset: bool = True, exclude_none: bool = True
    ) -> dict[str, Any]:
        """Smart export method that removes unsupported fields based on type.

        This method intelligently exports the model by:
        1. Using standard Pydantic model_dump with exclude options
        2. Removing fields that are not supported by the specific protocol type
        3. Ensuring compliance with sing-box specification

        Args:
            exclude_unset: Whether to exclude unset fields
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary representation suitable for sing-box configuration

        """
        data = self.model_dump(exclude_unset=exclude_unset, exclude_none=exclude_none)

        # Get the type field to determine protocol-specific cleanup
        protocol_type = data.get("type")
        if protocol_type:
            data = self._cleanup_by_type(data, protocol_type)

        return data

    def _cleanup_by_type(
        self, data: dict[str, Any], protocol_type: str
    ) -> dict[str, Any]:
        """Remove unsupported fields based on protocol type.

        Args:
            data: Model data dictionary
            protocol_type: Protocol type string

        Returns:
            Cleaned data dictionary

        """
        # Define which protocols support transport
        transport_supported = {
            "vmess",
            "vless",
            "trojan",
            "tuic",
            "hysteria2",
            "shadowsocks",
            "shadowtls",
        }

        # Define which protocols support TLS
        tls_supported = {
            "vmess",
            "vless",
            "trojan",
            "tuic",
            "hysteria2",
            "http",
            "shadowtls",
            "anytls",
            "naive",
        }

        # Remove transport if not supported
        if protocol_type not in transport_supported and "transport" in data:
            data.pop("transport", None)

        # Remove TLS if not supported
        if protocol_type not in tls_supported and "tls" in data:
            data.pop("tls", None)

        # Protocol-specific cleanup
        if protocol_type == "block":
            # Block outbound doesn't need server, port, etc.
            for field in ["server", "server_port", "tls", "transport", "multiplex"]:
                data.pop(field, None)

        elif protocol_type == "direct":
            # Direct outbound doesn't need TLS or transport
            for field in ["tls", "transport"]:
                data.pop(field, None)

        elif protocol_type == "dns":
            # DNS outbound doesn't need most fields
            for field in ["server", "server_port", "tls", "transport", "multiplex"]:
                data.pop(field, None)

        elif protocol_type == "selector":
            # Selector outbound doesn't need most fields
            for field in ["server", "server_port", "tls", "transport", "multiplex"]:
                data.pop(field, None)

        elif protocol_type == "urltest":
            # URLTest outbound doesn't need most fields
            for field in ["server", "server_port", "tls", "transport", "multiplex"]:
                data.pop(field, None)

        elif protocol_type == "mixed":
            # Mixed inbound doesn't support transport
            data.pop("transport", None)

        elif protocol_type == "socks":
            # SOCKS inbound doesn't support transport
            data.pop("transport", None)

        elif protocol_type == "http":
            # HTTP inbound doesn't support transport
            data.pop("transport", None)

        elif protocol_type == "shadowsocks":
            # Shadowsocks doesn't support transport or TLS
            for field in ["transport", "tls"]:
                data.pop(field, None)

        elif protocol_type == "tun":
            # TUN inbound doesn't support transport
            data.pop("transport", None)

        elif protocol_type == "redirect":
            # Redirect inbound doesn't support transport
            data.pop("transport", None)

        elif protocol_type == "tproxy":
            # TProxy inbound doesn't support transport
            data.pop("transport", None)

        return data
