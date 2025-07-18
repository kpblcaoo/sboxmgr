"""URI list parser for subscription data.

This module provides parsing functionality for URI-based subscription formats
that contain multiple server URIs in a single file. It supports various
protocols including Shadowsocks, VLess, VMess, and Trojan with proper
error handling and validation.
"""

import base64
import binascii
import json
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from sboxmgr.utils.env import get_debug_level

from ..base_parser import BaseParser
from ..models import ParsedServer
from ..registry import register

logger = logging.getLogger(__name__)


@register("parser_uri_list")
class URIListParser(BaseParser):
    """Parser for URI list format subscription data.

    This parser handles subscription data consisting of newline-separated
    proxy URIs. Each URI represents a single server configuration in a
    standardized URI format (vless://, vmess://, trojan://, ss://, etc.).

    Enhanced features:
    - Unicode/emoji support in tags, passwords, and usernames
    - Proper handling of spaces in passwords and usernames
    - Escaped character support
    - Very long line handling
    - Improved query parameter parsing
    - Better error recovery and fallback mechanisms
    """

    def parse(self, raw: bytes) -> list[ParsedServer]:
        """Parse URI list subscription data into ParsedServer objects.

        Args:
            raw: Raw bytes containing newline-separated proxy URIs.

        Returns:
            List[ParsedServer]: List of parsed server configurations.

        Raises:
            ValueError: If URI format is invalid or unsupported.
            UnicodeDecodeError: If raw data cannot be decoded as UTF-8.

        """
        try:
            lines = raw.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            # Fallback to latin-1 for very old or corrupted files
            lines = raw.decode("latin-1").splitlines()

        servers = []
        debug_level = get_debug_level()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle very long lines
            if len(line) > 10000:  # 10KB limit
                if debug_level > 0:
                    logger.warning(
                        f"Line {line_num} too long ({len(line)} chars), truncating"
                    )
                line = line[:10000]

            try:
                if line.startswith("ss://"):
                    ss = self._parse_ss(line)
                    if ss and ss.address != "invalid":
                        servers.append(ss)
                    elif debug_level > 0:
                        logger.warning(
                            f"Failed to parse ss:// line {line_num}: {line[:100]}..."
                        )
                elif line.startswith("vless://"):
                    vless = self._parse_vless(line)
                    if vless:
                        servers.append(vless)
                    elif debug_level > 0:
                        logger.warning(
                            f"Failed to parse vless:// line {line_num}: {line[:100]}..."
                        )
                elif line.startswith("vmess://"):
                    vmess = self._parse_vmess(line)
                    if vmess and vmess.address != "invalid":
                        servers.append(vmess)
                    elif debug_level > 0:
                        logger.warning(
                            f"Failed to parse vmess:// line {line_num}: {line[:100]}..."
                        )
                elif line.startswith("trojan://"):
                    trojan = self._parse_trojan(line)
                    if trojan:
                        servers.append(trojan)
                    elif debug_level > 0:
                        logger.warning(
                            f"Failed to parse trojan:// line {line_num}: {line[:100]}..."
                        )
                else:
                    if debug_level > 0:
                        logger.warning(
                            f"Ignored line {line_num} in uri list: {line[:100]}..."
                        )
                    servers.append(ParsedServer(type="unknown", address=line, port=0))
            except Exception as e:
                if debug_level > 0:
                    logger.error(f"Error parsing line {line_num}: {str(e)}")
                servers.append(
                    ParsedServer(
                        type="unknown", address=line, port=0, meta={"error": str(e)}
                    )
                )

        return servers

    def _parse_ss(self, line: str) -> Optional[ParsedServer]:
        """Parse shadowsocks URI into ParsedServer object.

        Enhanced support for:
        - Unicode/emoji in tags and passwords
        - Spaces in passwords and usernames
        - Escaped characters
        - Various query parameter formats
        - Base64 and plain text formats

        Args:
            line: Shadowsocks URI string

        Returns:
            ParsedServer object with parsed configuration or None if parsing fails

        """
        # Исправляем проблему с неправильным порядком # и ? в URL
        if "#" in line and "?" in line:
            hash_pos = line.find("#")
            query_pos = line.find("?")
            if query_pos > hash_pos:
                # ? после # - неправильный порядок, исправляем вручную
                scheme_part = line[:hash_pos]
                fragment_part = line[hash_pos + 1 : query_pos]
                query_part = line[query_pos + 1 :]

                # Создаём правильный URL для парсинга
                corrected_line = f"{scheme_part}?{query_part}#{fragment_part}"
                parsed = urlparse(corrected_line)
                tag = self._safe_unquote(fragment_part) if fragment_part else ""
                query = parse_qs(query_part)
            else:
                # Правильный порядок
                parsed = urlparse(line)
                tag = self._safe_unquote(parsed.fragment) if parsed.fragment else ""
                query = parse_qs(parsed.query)
        else:
            # Нет проблем с порядком
            parsed = urlparse(line)
            tag = self._safe_unquote(parsed.fragment) if parsed.fragment else ""
            query = parse_qs(parsed.query)

        uri = parsed.netloc + parsed.path

        try:
            method_pass, host_port = self._extract_ss_components(uri, line)
            if not method_pass or not host_port:
                return self._create_invalid_ss_server("failed to extract components")

            method, password = self._parse_ss_credentials(method_pass, line)
            if not method or not password:
                return self._create_invalid_ss_server("failed to parse credentials")

            host, port, endpoint_error = self._parse_ss_endpoint(host_port, line)
            if not host or port == 0:
                return self._create_invalid_ss_server(
                    endpoint_error or "failed to parse endpoint"
                )

            return self._create_ss_server(method, password, host, port, tag, query)

        except (ValueError, AttributeError, IndexError) as e:
            # Fallback to regex parsing if structured parsing fails
            return self._parse_ss_with_regex(uri, tag, query, line, str(e))

    def _safe_unquote(self, text: str) -> str:
        """Safely unquote URL-encoded text with fallback for malformed encoding."""
        try:
            return unquote(text)
        except (UnicodeDecodeError, ValueError):
            # Fallback for malformed URL encoding
            return text

    def _extract_ss_components(self, uri: str, line: str) -> tuple[str, str]:
        """Extract method:password and host:port components from SS URI.

        Enhanced to handle:
        - Unicode/emoji in passwords
        - Spaces in passwords
        - Malformed base64
        - Various encoding issues
        """
        debug_level = get_debug_level()

        # Try base64 decoding first
        if "@" in uri:
            b64, after = uri.split("@", 1)
            try:
                # Handle padding issues - only add padding if needed
                padding_needed = len(b64) % 4
                if padding_needed:
                    b64_padded = b64 + "=" * (4 - padding_needed)
                else:
                    b64_padded = b64
                decoded = base64.urlsafe_b64decode(b64_padded).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                # Fallback: treat as plain text
                decoded = b64

            if "@" in decoded:
                # Base64 decoded format: method:password@host:port
                parts = decoded.split("@", 1)
                return parts[0], parts[1]
            else:
                # Plain text format: method:password@host:port
                return decoded, after
        else:
            # Whole string is base64 or plain
            try:
                # Handle padding issues - only add padding if needed
                padding_needed = len(uri) % 4
                if padding_needed:
                    uri_padded = uri + "=" * (4 - padding_needed)
                else:
                    uri_padded = uri
                decoded = base64.urlsafe_b64decode(uri_padded).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                decoded = uri  # fallback: not base64

            if "@" in decoded:
                parts = decoded.split("@", 1)
                return parts[0], parts[1]
            else:
                if debug_level > 0:
                    logger.warning(f"ss:// no host in line: {line[:100]}...")
                return "", ""

    def _parse_ss_credentials(self, method_pass: str, line: str) -> tuple[str, str]:
        """Parse method and password from method:password string.

        Enhanced to handle:
        - Unicode/emoji in passwords
        - Spaces in passwords
        - Escaped characters
        """
        debug_level = get_debug_level()

        if ":" not in method_pass:
            if debug_level > 0:
                logger.warning(
                    f"ss:// parse failed (no colon in method:pass): {line[:100]}..."
                )
            return "", ""

        parts = method_pass.split(":", 1)
        method, password = parts[0], parts[1]

        # Handle URL-encoded passwords
        try:
            password = self._safe_unquote(password)
        except Exception:
            pass  # Keep original if unquote fails

        return method, password

    def _parse_ss_endpoint(self, host_port: str, line: str) -> tuple[str, int, str]:
        """Parse host and port from host:port string.

        Enhanced to handle:
        - IPv6 addresses
        - Unicode in hostnames
        - Various port formats
        """
        debug_level = get_debug_level()

        if ":" not in host_port:
            if debug_level > 0:
                logger.warning(
                    f"ss:// parse failed (no port specified): {line[:100]}..."
                )
            return "", 0, "no port specified"

        # Handle IPv6 addresses
        if host_port.startswith("[") and "]" in host_port:
            # IPv6 format: [::1]:port
            end_bracket = host_port.find("]")
            host = host_port[1:end_bracket]
            port_str = host_port[end_bracket + 2 :]  # Skip ]:
        else:
            # Regular format: host:port
            parts = host_port.split(":", 1)
            host, port_str = parts[0], parts[1]

        try:
            port = int(port_str)
            if port <= 0 or port > 65535:
                raise ValueError("Port out of range")
            return host, port, ""
        except ValueError:
            if debug_level > 0:
                logger.warning(
                    f"ss:// invalid port: {port_str} in line: {line[:100]}..."
                )
            return "", 0, "invalid port"

    def _create_ss_server(
        self, method: str, password: str, host: str, port: int, tag: str, query: dict
    ) -> ParsedServer:
        """Create ParsedServer object for shadowsocks configuration.

        Enhanced to handle:
        - Unicode/emoji in tags
        - Complex query parameters
        - Various metadata formats
        """
        meta = {"password": password}  # pragma: allowlist secret

        if tag:
            meta["tag"] = tag

        # Process query parameters
        for k, v in query.items():
            if v:
                # Handle multiple values for same key
                if len(v) == 1:
                    meta[k] = v[0]
                else:
                    meta[k] = v  # Keep as list if multiple values
            else:
                meta[k] = ""

        return ParsedServer(
            type="ss", address=host, port=port, security=method, meta=meta
        )

    def _create_invalid_ss_server(self, error: str) -> ParsedServer:
        """Create invalid ParsedServer for failed SS parsing."""
        return ParsedServer(type="ss", address="invalid", port=0, meta={"error": error})

    def _parse_ss_with_regex(
        self, uri: str, tag: str, query: dict, line: str, error: str
    ) -> ParsedServer:
        """Fallback SS parsing using regex pattern matching.

        Enhanced regex patterns for better edge case handling.
        """
        debug_level = get_debug_level()

        # Try multiple regex patterns for different formats
        patterns = [
            r"(?P<method>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)",  # Standard
            r"(?P<method>[^:]+):(?P<password>[^@]+)@\[(?P<host>[^\]]+)\]:?(?P<port>\d+)",  # IPv6
        ]

        for pattern in patterns:
            match = re.match(pattern, uri)
            if match:
                meta = {
                    "password": self._safe_unquote(match.group("password"))
                }  # pragma: allowlist secret
                if tag:
                    meta["tag"] = tag
                for k, v in query.items():
                    meta[k] = v[0] if v else ""
                return ParsedServer(
                    type="ss",
                    address=match.group("host"),
                    port=int(match.group("port")),
                    security=match.group("method"),
                    meta=meta,
                )

        if debug_level > 0:
            logger.warning(
                f"ss:// totally failed to parse: {line[:100]}... (error: {error})"
            )
        return self._create_invalid_ss_server(f"parse failed: {error}")

    def _parse_trojan(self, line: str) -> Optional[ParsedServer]:
        """Parse trojan URI with enhanced Unicode support."""
        try:
            parsed = urlparse(line)
            host, port = parsed.hostname, parsed.port or 0
            password = self._safe_unquote(parsed.username or "")
            params = parse_qs(parsed.query)
            tag = self._safe_unquote(parsed.fragment) if parsed.fragment else ""

            meta = {"tag": tag} if tag else {}
            meta["password"] = password
            for k, v in params.items():
                meta[k] = v[0] if v else ""

            return ParsedServer(
                type="trojan", address=host or "", port=port, security=None, meta=meta
            )
        except Exception as e:
            logger.warning(f"Failed to parse trojan URI: {str(e)}")
            return None

    def _parse_vless(self, line: str) -> Optional[ParsedServer]:
        """Parse vless URI with enhanced Unicode support."""
        try:
            parsed = urlparse(line)
            host, port = parsed.hostname, parsed.port or 0
            uuid = self._safe_unquote(parsed.username or "")
            params = parse_qs(parsed.query)
            label = self._safe_unquote(parsed.fragment) if parsed.fragment else ""

            meta = {"uuid": uuid, "label": label}  # pragma: allowlist secret
            for k, v in params.items():
                meta[k] = v[0] if v else ""

            return ParsedServer(
                type="vless",
                address=host or "",
                port=port,
                security=params.get("security", [None])[0],
                meta=meta,
            )
        except Exception as e:
            logger.warning(f"Failed to parse vless URI: {str(e)}")
            return None

    def _parse_vmess(self, line: str) -> Optional[ParsedServer]:
        """Parse vmess URI with enhanced error handling."""
        try:
            b64 = line[8:]
            # Handle padding issues - only add padding if needed
            padding_needed = len(b64) % 4
            if padding_needed:
                b64_padded = b64 + "=" * (4 - padding_needed)
            else:
                b64_padded = b64

            decoded = base64.urlsafe_b64decode(b64_padded).decode("utf-8")
            data = json.loads(decoded)

            return ParsedServer(
                type="vmess",
                address=data.get("add", ""),
                port=int(data.get("port", 0)),
                security=data.get("security"),
                meta=data,
            )
        except (
            binascii.Error,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
        ) as e:
            logger.warning(f"Failed to parse vmess URI: {str(e)}")
            return ParsedServer(
                type="vmess",
                address="invalid",
                port=0,
                meta={"error": f"decode failed: {type(e).__name__}"},
            )
