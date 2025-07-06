"""JSON subscription parser implementations.

This module provides parsers for JSON-format subscription data including
native JSON subscriptions and ShadowsocksR (SSR) JSON format. It handles
various JSON subscription formats and converts them into standardized
ParsedServer objects for consistent processing.
"""
import json
import re
from typing import List, Tuple
from ..models import ParsedServer
from ..base_parser import BaseParser
from sboxmgr.utils.env import get_debug_level
from ..registry import register

@register("json")
class JSONParser(BaseParser):
    """Parser for native JSON subscription format.

    This parser handles JSON subscription data with server arrays and
    converts them into ParsedServer objects. It supports various JSON
    subscription formats and provides robust error handling.
    """

    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Parse JSON subscription data into ParsedServer objects.

        Args:
            raw: Raw bytes containing JSON subscription data.

        Returns:
            List[ParsedServer]: List of parsed server configurations.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.
            KeyError: If required JSON fields are missing.

        """
        debug_level = get_debug_level()
        try:
            json.loads(raw.decode("utf-8"))
        except Exception as e:
            if debug_level >= 2:
                print(f"[WARN] JSON parse error: {e}")
            raise  # выбрасываем ошибку дальше
        # TODO: распарсить data в список ParsedServer (заглушка)
        return []

@register("tolerant_json")
class TolerantJSONParser(BaseParser):
    """Parser for JSON data with comments and formatting tolerance.

    This parser handles JSON subscription data that may contain comments,
    trailing commas, or other non-standard JSON formatting. It cleans
    the data before parsing to improve compatibility with various sources.
    """

    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Parse tolerant JSON subscription data into ParsedServer objects.

        Args:
            raw: Raw bytes containing JSON data with potential formatting issues.

        Returns:
            List[ParsedServer]: List of parsed server configurations.

        Raises:
            json.JSONDecodeError: If JSON parsing fails after cleaning.

        """
        debug_level = get_debug_level()
        clean_json, removed = self._strip_comments_and_validate(raw.decode("utf-8"))
        if removed and debug_level > 0:
            print(f"[TolerantJSONParser] Removed comments/fields: {removed}")
        try:
            json.loads(clean_json)
        except Exception as e:
            if debug_level > 0:
                print(f"[TolerantJSONParser] JSON parse error after cleaning: {e}")
            raise
        # TODO: распарсить data в список ParsedServer (заглушка)
        return []

    def _strip_comments_and_validate(self, raw_data: str) -> Tuple[str, list]:
        removed = []
        # Удаляем leading комментарии и шум до первой { или [
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
            # После старта JSON — обычная очистка
            if stripped_line.startswith("//") or stripped_line.startswith("#"):
                removed.append(line)
                continue
            # Удаляем inline // и # комментарии
            if '//' in line:
                idx = line.index('//')
                removed.append(line[idx:])
                line = line[:idx]
            if '#' in line and not line.lstrip().startswith('#'):
                idx = line.index('#')
                removed.append(line[idx:])
                line = line[:idx]
            clean_lines.append(line)
        clean_json = '\n'.join(clean_lines)
        # Удаляем поля _comment и trailing commas
        clean_json = re.sub(r'"_comment"\s*:\s*".*?",?', '', clean_json)
        clean_json = re.sub(r',\s*([}\]])', r'\1', clean_json)
        return clean_json, removed

@register("ssr_json")
class SSRJSONParser(BaseParser):
    """Parser for ShadowsocksR (SSR) JSON subscription format.

    This parser handles SSR-specific JSON format with SSR protocol
    configurations and converts them into standardized ParsedServer
    objects for compatibility with other subscription formats.
    """

    def parse(self, raw: bytes):
        """Parse SSR JSON subscription data into ParsedServer objects.

        Args:
            raw: Raw bytes containing SSR JSON subscription data.

        Returns:
            List[ParsedServer]: List of parsed SSR server configurations.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.
            KeyError: If required SSR fields are missing.

        """
        # TODO: implement SSR JSON parsing logic
        return []
