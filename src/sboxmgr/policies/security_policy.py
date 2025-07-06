"""Security policies for sboxmgr.

This module provides policies for security validation including
protocol security, encryption requirements, and authentication checks.
"""

from typing import Any, List, Optional

from .base import BasePolicy, PolicyContext, PolicyResult
from .utils import extract_metadata_field, validate_mode


class ProtocolPolicy(BasePolicy):
    """Policy for protocol security validation.

    Validates that servers use secure protocols and blocks
    potentially unsafe or deprecated protocols.
    """

    name = "ProtocolPolicy"
    description = "Validates protocol security"
    group = "security"

    def __init__(
        self,
        allowed_protocols: Optional[List[str]] = None,
        blocked_protocols: Optional[List[str]] = None,
        mode: str = "whitelist",
    ):
        """Initialize protocol policy.

        Args:
            allowed_protocols: List of allowed protocols (whitelist mode)
            blocked_protocols: List of blocked protocols (blacklist mode)
            mode: 'whitelist' or 'blacklist'

        Raises:
            ValueError: If mode is not 'whitelist' or 'blacklist'

        """
        super().__init__()
        validate_mode(mode, ["whitelist", "blacklist"])

        # Default secure protocols - include 'ss' as alias for shadowsocks
        self.allowed_protocols = set(
            allowed_protocols
            or ["vless", "trojan", "shadowsocks", "ss", "hysteria2", "tuic"]
        )

        # Default unsafe protocols
        self.blocked_protocols = set(
            blocked_protocols or ["http", "socks4", "socks5"]  # Unencrypted protocols
        )

        self.mode = mode

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate protocol security.

        Args:
            context: Context containing server information

        Returns:
            PolicyResult indicating if protocol is allowed

        """
        server = context.server

        if not server:
            return PolicyResult.allow("No server to check")

        # Extract protocol from server
        protocol = self._extract_protocol(server)
        if not protocol:
            return PolicyResult.allow("No protocol information available")

        # Apply policy based on mode
        if self.mode == "whitelist":
            if self.allowed_protocols and protocol not in self.allowed_protocols:
                return PolicyResult.deny(
                    f"Protocol {protocol} not in allowed list",
                    protocol=protocol,
                    allowed_protocols=list(self.allowed_protocols),
                )
        elif self.mode == "blacklist":
            if protocol in self.blocked_protocols:
                return PolicyResult.deny(
                    f"Protocol {protocol} is blocked",
                    protocol=protocol,
                    blocked_protocols=list(self.blocked_protocols),
                )

        return PolicyResult.allow(f"Protocol {protocol} is allowed")

    def _extract_protocol(self, server: Any) -> Optional[str]:
        """Extract protocol from server object.

        Args:
            server: Server object to extract protocol from

        Returns:
            Protocol name or None if not found

        """
        protocol = extract_metadata_field(
            server, "protocol", fallback_fields=["type", "method"]
        )
        return str(protocol).lower() if protocol else None


class EncryptionPolicy(BasePolicy):
    """Policy for encryption requirements validation.

    Ensures that servers use strong encryption methods
    and blocks weak or deprecated encryption.
    """

    name = "EncryptionPolicy"
    description = "Validates encryption strength"
    group = "security"

    def __init__(
        self,
        strong_encryption: Optional[List[str]] = None,
        weak_encryption: Optional[List[str]] = None,
        require_encryption: bool = True,
    ):
        """Initialize encryption policy.

        Args:
            strong_encryption: List of strong encryption methods
            weak_encryption: List of weak encryption methods
            require_encryption: Whether encryption is required

        """
        super().__init__()

        # Default strong encryption methods - include Reality/TLS variants
        self.strong_encryption = set(
            strong_encryption
            or [
                "tls",
                "reality",
                "xtls",
                "aes-256-gcm",
                "chacha20-poly1305",
                "chacha20-ietf-poly1305",
                "aes-256-gcm",
                "aes-128-gcm",
            ]
        )

        # Default weak encryption methods
        self.weak_encryption = set(
            weak_encryption or ["none", "plain", "aes-128", "rc4"]
        )

        self.require_encryption = require_encryption

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate encryption requirements.

        Args:
            context: Context containing server information

        Returns:
            PolicyResult indicating if encryption is acceptable

        """
        server = context.server

        if not server:
            return PolicyResult.allow("No server to check")

        # Extract encryption method from server
        encryption = self._extract_encryption(server)

        if not encryption:
            if self.require_encryption:
                return PolicyResult.deny("Encryption is required but not specified")
            return PolicyResult.allow("No encryption specified (not required)")

        # Check if encryption is weak
        if encryption in self.weak_encryption:
            return PolicyResult.deny(
                f"Weak encryption method: {encryption}",
                encryption=encryption,
                weak_methods=list(self.weak_encryption),
            )

        # Check if encryption is strong
        if encryption in self.strong_encryption:
            return PolicyResult.allow(f"Strong encryption: {encryption}")

        # Unknown encryption method
        return PolicyResult.allow(f"Unknown encryption method: {encryption}")

    def _extract_encryption(self, server: Any) -> Optional[str]:
        """Extract encryption method from server object.

        Args:
            server: Server object to extract encryption from

        Returns:
            Encryption method or None if not found

        """
        # Try direct fields first
        encryption = extract_metadata_field(
            server, "encryption", fallback_fields=["security", "cipher", "method"]
        )

        if encryption:
            return str(encryption).lower()

        # For VLESS/Reality servers, check for TLS/Reality indicators
        if hasattr(server, "meta") and isinstance(server.meta, dict):
            meta = server.meta

            # Check for Reality/TLS indicators
            if meta.get("tls") or meta.get("reality-opts"):
                return "reality"

            # Check for other TLS indicators
            if meta.get("servername") or meta.get("alpn"):
                return "tls"

        return None


class AuthenticationPolicy(BasePolicy):
    """Policy for authentication requirements validation.

    Ensures that servers use proper authentication methods
    and validates authentication credentials.
    """

    name = "AuthenticationPolicy"
    description = "Validates authentication methods"
    group = "security"

    def __init__(
        self,
        required_auth: bool = True,
        allowed_auth_methods: Optional[List[str]] = None,
        min_password_length: int = 8,
    ):
        """Initialize authentication policy.

        Args:
            required_auth: Whether authentication is required
            allowed_auth_methods: List of allowed authentication methods
            min_password_length: Minimum password length

        """
        super().__init__()
        self.required_auth = required_auth
        self.allowed_auth_methods = set(
            allowed_auth_methods or ["password", "uuid", "psk", "certificate"]
        )
        self.min_password_length = min_password_length

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate authentication requirements.

        Args:
            context: Context containing server information

        Returns:
            PolicyResult indicating if authentication is acceptable

        """
        server = context.server

        if not server:
            return PolicyResult.allow("No server to check")

        # Extract authentication info from server
        auth_method = self._extract_auth_method(server)
        auth_credentials = self._extract_auth_credentials(server)

        if not auth_method and not auth_credentials:
            if self.required_auth:
                return PolicyResult.deny("Authentication is required but not specified")
            return PolicyResult.allow("No authentication specified (not required)")

        # Check authentication method
        if auth_method and self.allowed_auth_methods:
            if auth_method not in self.allowed_auth_methods:
                return PolicyResult.deny(
                    f"Authentication method {auth_method} not allowed",
                    auth_method=auth_method,
                    allowed_methods=list(self.allowed_auth_methods),
                )

        # Check credentials strength
        if auth_credentials:
            if len(auth_credentials) < self.min_password_length:
                return PolicyResult.deny(
                    f"Credentials too short: {len(auth_credentials)} < {self.min_password_length}",
                    credential_length=len(auth_credentials),
                    min_length=self.min_password_length,
                )

        return PolicyResult.allow("Authentication requirements met")

    def _extract_auth_method(self, server: Any) -> Optional[str]:
        """Extract authentication method from server object.

        Args:
            server: Server object to extract auth method from

        Returns:
            Authentication method or None if not found

        """
        method = extract_metadata_field(
            server, "auth_method", fallback_fields=["authentication", "auth_type"]
        )
        return str(method).lower() if method else None

    def _extract_auth_credentials(self, server: Any) -> Optional[str]:
        """Extract authentication credentials from server object.

        Args:
            server: Server object to extract credentials from

        Returns:
            Credentials or None if not found

        """
        # Try direct fields first
        credentials = extract_metadata_field(
            server, "password", fallback_fields=["uuid", "psk", "secret", "token"]
        )

        if credentials:
            return str(credentials)

        # For VLESS servers, check meta.uuid
        if hasattr(server, "meta") and isinstance(server.meta, dict):
            meta = server.meta
            if meta.get("uuid"):
                return str(meta["uuid"])
            # For Shadowsocks servers, check meta.password
            if meta.get("password"):
                return str(meta["password"])

        return None
