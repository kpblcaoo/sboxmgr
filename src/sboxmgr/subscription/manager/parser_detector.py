"""Parser auto-detection functionality."""

import base64
import json
import logging
import re
from typing import Any, Optional, Protocol


class ParserProtocol(Protocol):
    """Protocol for parser objects that can parse subscription data."""

    def parse(self, raw: bytes) -> list[Any]:
        """Parse raw subscription data into server configurations."""
        ...


def detect_parser(raw: bytes, source_type: str) -> Optional[ParserProtocol]:
    """Auto-detect appropriate parser based on data content.

    Args:
        raw: Raw subscription data bytes.
        source_type: Subscription source type hint.

    Returns:
        Parser instance or None if detection fails.

    """
    # Декодируем данные
    text = raw.decode("utf-8", errors="ignore")

    # Если source_type явно указан, используем соответствующий парсер
    explicit_parser = _get_explicit_parser(source_type)
    if explicit_parser:
        return explicit_parser

    # Автоопределение по содержимому (fallback)
    return _auto_detect_parser(text)


def _get_explicit_parser(source_type: str) -> Optional[ParserProtocol]:
    """Get parser based on explicit source type.

    Args:
        source_type: Subscription source type hint.

    Returns:
        Parser instance or None if type not recognized.

    """
    if source_type in ("url_json", "file_json"):
        from ..parsers.singbox_parser import SingBoxParser

        return SingBoxParser()
    elif source_type in ("url_base64", "file_base64"):
        from ..parsers.base64_parser import Base64Parser

        return Base64Parser()
    elif source_type in ("uri_list", "file_uri_list"):
        from ..parsers.uri_list_parser import URIListParser

        return URIListParser()

    return None


def _auto_detect_parser(text: str) -> ParserProtocol:
    """Auto-detect parser based on content analysis.

    Args:
        text: Decoded subscription data text.

    Returns:
        Parser instance (fallback to Base64Parser if detection fails).

    """
    # 1. Пробуем JSON (SingBox)
    json_parser = _try_json_parser(text)
    if json_parser:
        return json_parser

    # 2. Пробуем Clash YAML
    clash_parser = _try_clash_parser(text)
    if clash_parser:
        return clash_parser

    # 3. Пробуем base64
    base64_parser = _try_base64_parser(text)
    if base64_parser:
        return base64_parser

    # 4. Пробуем plain URI list
    uri_parser = _try_uri_list_parser(text)
    if uri_parser:
        return uri_parser

    # Fallback
    from ..parsers.base64_parser import Base64Parser

    return Base64Parser()


def _try_json_parser(text: str) -> Optional[ParserProtocol]:
    """Try to detect JSON parser.

    Args:
        text: Text to analyze.

    Returns:
        SingBoxParser if JSON detected, None otherwise.

    """
    try:
        from ..parsers.singbox_parser import SingBoxParser

        parser = SingBoxParser()
        data = parser._strip_comments_and_validate(text)[0]
        json.loads(data)
        return parser
    except Exception as e:
        logging.debug(f"JSON parser detection failed: {e}")
        return None


def _try_clash_parser(text: str) -> Optional[ParserProtocol]:
    """Try to detect Clash YAML parser.

    Args:
        text: Text to analyze.

    Returns:
        ClashParser if Clash format detected, None otherwise.

    """
    # Check for Clash YAML indicators
    clash_indicators = [
        "mixed-port:",
        "proxies:",
        "proxy-groups:",
        "proxy-providers:",
        "rules:",
        "rule-providers:",
        "dns:",
    ]

    if any(indicator in text for indicator in clash_indicators):
        from ..parsers.clash_parser import ClashParser

        return ClashParser()

    return None


def _try_base64_parser(text: str) -> Optional[ParserProtocol]:
    """Try to detect base64 parser.

    Args:
        text: Text to analyze.

    Returns:
        Base64Parser if base64 detected, None otherwise.

    """
    # Check if text looks like base64
    b64_re = re.compile(r"^[A-Za-z0-9+/=\s]+$")
    if not (b64_re.match(text) and len(text.strip()) > 100):
        return None

    try:
        decoded = base64.b64decode(text.strip() + "=" * (-len(text.strip()) % 4))
        decoded_text = decoded.decode("utf-8", errors="ignore")

        # Check for proxy protocol indicators
        proxy_protocols = ("vless://", "vmess://", "trojan://", "ss://")
        if any(proto in decoded_text for proto in proxy_protocols):
            from ..parsers.base64_parser import Base64Parser

            return Base64Parser()
    except Exception as e:
        logging.debug(f"Base64 parser detection failed: {e}")

    return None


def _try_uri_list_parser(text: str) -> Optional[ParserProtocol]:
    """Try to detect URI list parser.

    Args:
        text: Text to analyze.

    Returns:
        URIListParser if URI list detected, None otherwise.

    """
    lines = text.splitlines()
    proxy_protocols = ("vless://", "vmess://", "trojan://", "ss://")

    if any(line.strip().startswith(proxy_protocols) for line in lines):
        from ..parsers.uri_list_parser import URIListParser

        return URIListParser()

    return None
