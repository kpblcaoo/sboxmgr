import base64
import re
from typing import List
from ..models import ParsedServer
from ..base_parser import BaseParser
from .uri_list_parser import URIListParser
from sboxmgr.utils.env import get_debug_level

class Base64Parser(BaseParser):
    def parse(self, raw: bytes) -> List[ParsedServer]:
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