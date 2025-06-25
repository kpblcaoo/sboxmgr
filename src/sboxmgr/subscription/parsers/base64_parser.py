"""Base64-encoded subscription parser implementation.

This module provides the Base64Parser class for parsing base64-encoded
subscription data. It handles base64 decoding and delegates to appropriate
parsers based on the decoded content format (URI lists, JSON, YAML, etc.).
"""
import base64
import re
from typing import List
from ..models import ParsedServer
from ..base_parser import BaseParser
from .uri_list_parser import URIListParser
from sboxmgr.utils.env import get_debug_level
from ..registry import register

@register("base64")
class Base64Parser(BaseParser):
    """Parser for base64-encoded subscription data.
    
    Handles the most common subscription format where proxy configurations
    are base64-encoded and contain URI-style proxy links. Supports various
    proxy protocols including ss://, vless://, vmess://, and legacy formats.
    
    Features:
    - Automatic base64 decoding
    - URI protocol detection and delegation
    - Legacy shadowsocks format support (auto-prefix ss://)
    - Comment line filtering (lines starting with #)
    - Debug output for unsupported formats
    """
    
    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Parse base64-encoded subscription data into server configurations.
        
        Decodes base64 content, splits into lines, and processes each line
        as a proxy URI. Delegates actual URI parsing to URIListParser.
        
        Args:
            raw: Base64-encoded subscription data.
            
        Returns:
            List of ParsedServer objects from all valid proxy URIs.
            
        Note:
            Automatically adds "ss://" prefix to legacy shadowsocks format
            lines that match the pattern "method:password@server:port".
        """
        decoded = base64.b64decode(raw)
        lines = decoded.decode("utf-8").splitlines()
        servers = []
        debug_level = get_debug_level()
        ss_pattern = re.compile(r'^[^:]+:[^@]+@[^:]+:\d+$')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith(('ss://', 'vless://', 'vmess://')):
                servers.extend(URIListParser().parse(line.encode("utf-8")))
            elif ss_pattern.match(line):
                if debug_level > 1:
                    print(f"[WARN] Adding ss:// prefix to legacy base64 line: {line}")
                servers.extend(URIListParser().parse(f"ss://{line}".encode("utf-8")))
            else:
                if debug_level > 1:
                    print(f"[WARN] Ignored line in base64 subscription: {line}")
                continue
        return servers 