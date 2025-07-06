"""Sing-box JSON configuration parser implementation.

This module provides the SingBoxParser class for parsing sing-box JSON
configuration files. It handles the native sing-box format with outbounds
and converts them into standardized ParsedServer objects.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sboxmgr.utils.env import get_debug_level

from ..base_parser import BaseParser
from ..models import ParsedServer
from ..registry import register


@register("singbox")
class SingBoxParser(BaseParser):
    """Parser for sing-box JSON configuration format.

    This parser handles sing-box JSON configuration files and extracts
    server configurations from the outbounds section. It supports both
    modern and legacy sing-box syntax with safe field injection and
    fail-tolerance.
    """

    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Parse sing-box JSON configuration into ParsedServer objects.

        Args:
            raw: Raw bytes containing sing-box JSON configuration.

        Returns:
            List[ParsedServer]: List of parsed server configurations.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.

        """
        debug_level = get_debug_level()

        try:
            # Clean and parse JSON
            clean_json, removed = self._strip_comments_and_validate(raw.decode("utf-8"))
            if removed and debug_level > 0:
                print(f"[SingBoxParser] Removed comments/fields: {removed}")

            config = json.loads(clean_json)

            # Extract outbounds
            outbounds = config.get("outbounds", [])
            if not outbounds:
                if debug_level > 0:
                    print("[SingBoxParser] No outbounds found in configuration")
                return []

            servers = []
            for i, outbound in enumerate(outbounds):
                try:
                    server = self._parse_outbound(outbound, i)
                    if server:
                        servers.append(server)
                except Exception as e:
                    if debug_level > 0:
                        print(f"[SingBoxParser] Failed to parse outbound {i}: {e}")
                    continue

            if debug_level > 0:
                print(
                    f"[SingBoxParser] Parsed {len(servers)} servers from {len(outbounds)} outbounds"
                )

            return servers

        except Exception as e:
            if debug_level > 0:
                print(f"[SingBoxParser] Parse error: {e}")
            raise

    def _strip_comments_and_validate(self, raw_data: str) -> Tuple[str, list]:
        """Strip comments and validate JSON data.

        Args:
            raw_data: Raw JSON string with potential comments.

        Returns:
            Tuple[str, list]: Clean JSON string and list of removed items.

        """
        removed = []

        # Remove leading comments and noise before first { or [
        lines = raw_data.splitlines()
        clean_lines = []
        found_json_start = False

        for line in lines:
            stripped_line = line.strip()
            if not found_json_start:
                if stripped_line.startswith("{") or stripped_line.startswith("["):
                    found_json_start = True
                    clean_lines.append(line)
                else:
                    removed.append(line)
                continue

            # After JSON start - normal cleaning
            if stripped_line.startswith("//") or stripped_line.startswith("#"):
                removed.append(line)
                continue

            # Remove inline // and # comments
            if "//" in line:
                idx = line.index("//")
                removed.append(line[idx:])
                line = line[:idx]
            if "#" in line and not line.lstrip().startswith("#"):
                idx = line.index("#")
                removed.append(line[idx:])
                line = line[:idx]

            clean_lines.append(line)

        clean_json = "\n".join(clean_lines)

        # Remove _comment fields and trailing commas
        clean_json = re.sub(r'"_comment"\s*:\s*".*?",?', "", clean_json)
        clean_json = re.sub(r",\s*([}\]])", r"\1", clean_json)

        return clean_json, removed

    def _parse_outbound(self, outbound: dict, index: int = 0) -> Optional[ParsedServer]:
        """Parse a single outbound configuration into ParsedServer.

        Args:
            outbound: Outbound configuration dictionary.
            index: Index of outbound for tracing.

        Returns:
            ParsedServer: Parsed server configuration or None if not a server.

        """
        outbound_type = outbound.get("type", "")

        # Skip non-server outbounds (based on validator structure)
        if outbound_type in ["direct", "block", "dns", "urltest", "selector"]:
            return None

        # Extract common fields with fail-tolerance
        tag = outbound.get("tag", "")
        server = outbound.get("server", "")
        port_raw = outbound.get("server_port")

        # Fail-tolerance: require server and port
        if not server or not port_raw:
            return None

        # Validate port type and convert
        try:
            port = int(port_raw)
            if port <= 0 or port > 65535:
                return None
        except (ValueError, TypeError):
            return None

        # Parse by protocol type (based on validator structure)
        if outbound_type == "shadowsocks":
            return self._parse_shadowsocks_outbound(outbound, tag, server, port, index)
        elif outbound_type == "vmess":
            return self._parse_vmess_outbound(outbound, tag, server, port, index)
        elif outbound_type == "vless":
            return self._parse_vless_outbound(outbound, tag, server, port, index)
        elif outbound_type == "trojan":
            return self._parse_trojan_outbound(outbound, tag, server, port, index)
        elif outbound_type == "hysteria":
            return self._parse_hysteria_outbound(outbound, tag, server, port, index)
        elif outbound_type == "tuic":
            return self._parse_tuic_outbound(outbound, tag, server, port, index)
        elif outbound_type == "wireguard":
            return self._parse_wireguard_outbound(outbound, tag, server, port, index)
        elif outbound_type == "http":
            return self._parse_http_outbound(outbound, tag, server, port, index)
        elif outbound_type == "socks":
            return self._parse_socks_outbound(outbound, tag, server, port, index)
        else:
            # Unknown protocol - create basic server with safe metadata
            meta = self._create_safe_meta(
                {"tag": tag, "origin": "singbox", "chain": "outbound"}
            )
            return ParsedServer(
                type=outbound_type, address=server, port=port, security=None, meta=meta
            )

    def _create_safe_meta(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create safe metadata dictionary filtering out None values.

        Args:
            fields: Dictionary of potential metadata fields.

        Returns:
            Dict[str, Any]: Clean metadata with only non-None values.

        """
        return {k: v for k, v in fields.items() if v is not None}

    def _parse_shadowsocks_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse shadowsocks outbound configuration."""
        method = outbound.get("method", "")
        password = outbound.get("password", "")

        meta = self._create_safe_meta(
            {
                "password": password,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"ss_{index}",
            }
        )

        return ParsedServer(
            type="ss", address=server, port=port, security=method, meta=meta
        )

    def _parse_vmess_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse vmess outbound configuration."""
        uuid = outbound.get("uuid", "")
        security = outbound.get("security", "auto")

        meta = self._create_safe_meta(
            {
                "uuid": uuid,
                "security": security,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"vmess_{index}",
            }
        )

        return ParsedServer(
            type="vmess", address=server, port=port, security=security, meta=meta
        )

    def _parse_vless_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse vless outbound configuration."""
        uuid = outbound.get("uuid", "")
        security = outbound.get("security", "none")
        flow = outbound.get("flow", "")

        meta = self._create_safe_meta(
            {
                "uuid": uuid,
                "security": security,
                "flow": flow,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"vless_{index}",
            }
        )

        return ParsedServer(
            type="vless", address=server, port=port, security=security, meta=meta
        )

    def _parse_trojan_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse trojan outbound configuration."""
        password = outbound.get("password", "")
        flow = outbound.get("flow", "")

        meta = self._create_safe_meta(
            {
                "password": password,
                "flow": flow,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"trojan_{index}",
            }
        )

        return ParsedServer(
            type="trojan", address=server, port=port, security="tls", meta=meta
        )

    def _parse_hysteria_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse hysteria outbound configuration."""
        auth = outbound.get("auth", "")
        up_mbps = outbound.get("up_mbps", 100)
        down_mbps = outbound.get("down_mbps", 100)

        meta = self._create_safe_meta(
            {
                "auth": auth,
                "up_mbps": up_mbps,
                "down_mbps": down_mbps,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"hysteria_{index}",
            }
        )

        return ParsedServer(
            type="hysteria", address=server, port=port, security="udp", meta=meta
        )

    def _parse_tuic_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse tuic outbound configuration."""
        uuid = outbound.get("uuid", "")
        password = outbound.get("password", "")
        congestion_control = outbound.get("congestion_control", "bbr")

        meta = self._create_safe_meta(
            {
                "uuid": uuid,
                "password": password,
                "congestion_control": congestion_control,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"tuic_{index}",
            }
        )

        return ParsedServer(
            type="tuic", address=server, port=port, security="udp", meta=meta
        )

    def _parse_wireguard_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse wireguard outbound configuration."""
        private_key = outbound.get("private_key", "")
        peer_public_key = outbound.get("peer_public_key", "")
        pre_shared_key = outbound.get("pre_shared_key", "")

        meta = self._create_safe_meta(
            {
                "private_key": private_key,
                "peer_public_key": peer_public_key,
                "pre_shared_key": pre_shared_key,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"wireguard_{index}",
            }
        )

        return ParsedServer(
            type="wireguard", address=server, port=port, security="udp", meta=meta
        )

    def _parse_http_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse http outbound configuration."""
        username = outbound.get("username", "")
        password = outbound.get("password", "")

        meta = self._create_safe_meta(
            {
                "username": username,
                "password": password,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"http_{index}",
            }
        )

        return ParsedServer(
            type="http", address=server, port=port, security="http", meta=meta
        )

    def _parse_socks_outbound(
        self, outbound: dict, tag: str, server: str, port: int, index: int
    ) -> ParsedServer:
        """Parse socks outbound configuration."""
        username = outbound.get("username", "")
        password = outbound.get("password", "")

        meta = self._create_safe_meta(
            {
                "username": username,
                "password": password,
                "tag": tag,
                "origin": "singbox",
                "chain": "outbound",
                "server_id": f"socks_{index}",
            }
        )

        return ParsedServer(
            type="socks", address=server, port=port, security="socks", meta=meta
        )
