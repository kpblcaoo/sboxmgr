"""Clash configuration parser implementation.

This module provides the ClashParser class for parsing Clash-format YAML
subscription data. It converts Clash proxy configurations into standardized
ParsedServer objects for consistent processing across different client formats.
"""
import yaml
from ..models import ParsedServer
from ..base_parser import BaseParser
from ..registry import register

@register("clash")
class ClashParser(BaseParser):
    """Parser for Clash-format YAML subscription data.
    
    This parser handles Clash-specific proxy configurations and converts them
    into standardized ParsedServer objects. It supports various Clash proxy
    types including shadowsocks, vmess, trojan, and others.
    """
    
    def parse(self, raw: bytes):
        """Parse Clash YAML subscription data into ParsedServer objects.
        
        Args:
            raw: Raw bytes containing Clash YAML configuration data.
            
        Returns:
            List[ParsedServer]: List of parsed server configurations.
            
        Raises:
            yaml.YAMLError: If YAML parsing fails.
            KeyError: If required configuration fields are missing.

        """
        try:
            data = yaml.safe_load(raw.decode("utf-8"))
        except Exception as e:
            print(f"[ClashParser] YAML parse error: {e}")
            return []
        servers = []
        proxies = []
        # Если это список — возможно, это просто список прокси
        if isinstance(data, list):
            proxies = data
        # Если это dict — ищем секцию proxies
        elif isinstance(data, dict):
            proxies = data.get("proxies") or data.get("Proxy") or []
        else:
            print(f"[ClashParser] Unexpected YAML root type: {type(data)}")
            return []
        if not proxies:
            print("[ClashParser] No proxies section found or section is empty.")
            return []
        for p in proxies:
            servers.append(ParsedServer(
                type=p.get("type", "unknown"),
                address=p.get("server", ""),
                port=int(p.get("port", 0)),
                security=p.get("cipher", None),
                meta=p
            ))
        # Убираем безусловный print - логирование будет в manager.py
        return servers
