"""Security enrichment functionality for server data."""

from typing import Any, Dict, List

from ...models import ParsedServer, PipelineContext


class SecurityEnricher:
    """Provides security-related metadata enrichment for servers.

    Adds security indicators like encryption level, port classification,
    protocol vulnerabilities, and recommended security settings.
    """

    def __init__(self):
        """Initialize security enricher."""
        pass

    def enrich(self, server: ParsedServer, context: PipelineContext) -> ParsedServer:
        """Apply security enrichment to a server.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with security enrichment applied
        """
        security_info = {}

        try:
            security_info.update(
                {
                    "encryption_level": self._get_encryption_level(server),
                    "port_classification": self._classify_port(server.port),
                    "protocol_vulnerabilities": self._get_protocol_vulnerabilities(
                        server.type
                    ),
                    "recommended_settings": self._get_recommended_settings(server),
                }
            )

        except Exception as e:
            security_info["error"] = str(e)

        if security_info:
            server.meta["security"] = security_info

        return server

    def _get_encryption_level(self, server: ParsedServer) -> str:
        """Get encryption level for server.

        Args:
            server: Server to analyze

        Returns:
            Encryption level ('strong', 'moderate', 'weak', 'none')
        """
        if hasattr(server, "security") and server.security:
            # Strong encryption
            if server.security in ["tls", "reality", "xtls"]:
                return "strong"
            # Moderate encryption
            elif server.security in [
                "auto",
                "aes-256-gcm",
                "chacha20-poly1305",
                "aes-128-gcm",
            ]:
                return "moderate"
            # No encryption
            elif server.security in ["none"]:
                return "none"
            # Weak encryption (deprecated methods)
            else:
                return "weak"

        # Default based on protocol
        protocol_encryption = {
            "wireguard": "strong",
            "vless": "moderate",  # Depends on transport
            "vmess": "moderate",  # Depends on settings
            "trojan": "strong",
            "hysteria2": "strong",
            "tuic": "strong",
            "shadowtls": "strong",
            "shadowsocks": "moderate",
            "ss": "moderate",
            "http": "none",
            "socks": "none",
            "socks5": "none",
        }

        return protocol_encryption.get(server.type.lower(), "weak")

    def _classify_port(self, port: int) -> str:
        """Classify port type for security analysis.

        Args:
            port: Port number

        Returns:
            Port classification
        """
        # Well-known secure ports
        if port in [443, 8443]:
            return "https"
        # Well-known insecure ports
        elif port in [80, 8080]:
            return "http"
        # SOCKS proxy ports
        elif port == 1080:
            return "socks"
        # VPN ports
        elif port == 1194:
            return "openvpn"
        elif port == 51820:
            return "wireguard"
        # User/high ports (generally safer)
        elif 1024 <= port <= 65535:
            return "high"
        # System/privileged ports
        elif 1 <= port <= 1023:
            return "system"
        else:
            return "unknown"

    def _get_protocol_vulnerabilities(self, protocol_type: str) -> List[str]:
        """Get known vulnerabilities for protocol.

        Args:
            protocol_type: Protocol type

        Returns:
            List of vulnerability descriptions
        """
        vulnerabilities = {
            "vmess": ["timing_attack_v1", "weak_uuid_generation", "aead_deprecation"],
            "shadowsocks": ["replay_attack", "traffic_analysis", "weak_obfuscation"],
            "http": ["no_encryption", "plain_text", "man_in_the_middle"],
            "socks": ["no_authentication", "plain_text", "connection_tracking"],
            "socks5": [
                "weak_authentication",
                "plain_text_username_password",
                "connection_tracking",
            ],
        }

        return vulnerabilities.get(protocol_type.lower(), [])

    def _get_recommended_settings(self, server: ParsedServer) -> Dict[str, Any]:
        """Get recommended security settings for server.

        Args:
            server: Server to analyze

        Returns:
            Dictionary with recommended settings
        """
        recommendations = {}
        protocol = server.type.lower()

        if protocol == "vmess":
            recommendations.update(
                {
                    "alterId": 0,  # Disable deprecated alterId
                    "security": "auto",
                    "network": "ws",
                    "tls": True,
                    "encryption": "auto",
                }
            )
        elif protocol in ["shadowsocks", "ss"]:
            recommendations.update(
                {
                    "method": "aes-256-gcm",  # Strong encryption
                    "plugin": "v2ray-plugin",
                    "plugin_opts": {"mode": "websocket", "tls": True},
                }
            )
        elif protocol == "vless":
            recommendations.update(
                {
                    "flow": "xtls-rprx-vision",  # Modern flow control
                    "security": "tls",
                    "encryption": "none",  # VLESS doesn't need additional encryption
                }
            )
        elif protocol == "trojan":
            recommendations.update(
                {"security": "tls", "alpn": ["h2", "http/1.1"], "verify_cert": True}
            )
        elif protocol == "wireguard":
            recommendations.update(
                {"mtu": 1420, "keepalive": 25, "use_pre_shared_key": True}
            )
        elif protocol == "hysteria2":
            recommendations.update(
                {"obfuscation": "salamander", "bandwidth_limit": "auto"}
            )

        # General security recommendations
        recommendations.update(
            {
                "use_cdn": True if server.port in [80, 443, 8080, 8443] else False,
                "enable_mux": True,
                "test_url": "https://www.gstatic.com/generate_204",
            }
        )

        return recommendations
