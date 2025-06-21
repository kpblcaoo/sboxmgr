import base64
import re
from typing import List
from urllib.parse import urlparse, parse_qs, unquote
from ..models import ParsedServer
from ..base_parser import BaseParser
from sboxmgr.utils.env import get_debug_level

class URIListParser(BaseParser):
    def parse(self, raw: bytes) -> List[ParsedServer]:
        lines = raw.decode("utf-8").splitlines()
        servers = []
        debug_level = get_debug_level()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('ss://'):
                servers.append(self._parse_ss(line))
            elif line.startswith('vless://'):
                servers.append(self._parse_vless(line))
            elif line.startswith('vmess://'):
                servers.append(self._parse_vmess(line))
            else:
                if debug_level > 1:
                    print(f"[WARN] Ignored line in uri list: {line}")
                servers.append(ParsedServer(type="unknown", address=line, port=0))
        return servers

    def _parse_ss(self, line: str) -> ParsedServer:
        # ss://<base64>[@host:port][#tag][?query] или ss://method:password@host:port[#tag]
        parsed = urlparse(line)
        uri = parsed.netloc + parsed.path
        tag = unquote(parsed.fragment) if parsed.fragment else ""
        query = parse_qs(parsed.query)
        # Попытка декодировать как base64
        decoded = None
        try:
            # Если есть @, base64 до @, иначе вся строка
            if '@' in uri:
                b64, after = uri.split('@', 1)
                decoded = base64.urlsafe_b64decode(b64 + '=' * (-len(b64) % 4)).decode('utf-8')
                # decoded: method:password
                method_pass = decoded
                host_port = after
            else:
                # Вся строка — base64
                decoded = base64.urlsafe_b64decode(uri + '=' * (-len(uri) % 4)).decode('utf-8')
                # decoded: method:password@host:port
                if '@' in decoded:
                    method_pass, host_port = decoded.split('@', 1)
                else:
                    return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "no host in ss://"})
            if ':' not in method_pass or ':' not in host_port:
                return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "parse failed"})
            method, password = method_pass.split(':', 1)
            host, port = host_port.split(':', 1)
            meta = {"password": password}  # pragma: allowlist secret
            if tag:
                meta["tag"] = tag
            for k, v in query.items():
                meta[k] = v[0] if v else ""
            return ParsedServer(
                type="ss",
                address=host,
                port=int(port),
                security=method,
                meta=meta
            )
        except Exception:
            # Если не base64, пробуем как ss://method:[password]@host:port
            match = re.match(r'(?P<method>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)', uri)
            if not match:
                return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "parse failed"})
            meta = {"password": match.group('password')}  # pragma: allowlist secret
            if tag:
                meta["tag"] = tag
            for k, v in query.items():
                meta[k] = v[0] if v else ""
            return ParsedServer(
                type="ss",
                address=match.group('host'),
                port=int(match.group('port')),
                security=match.group('method'),
                meta=meta
            )

    def _parse_vless(self, line: str) -> ParsedServer:
        # vless://uuid@host:port?params#label
        parsed = urlparse(line)
        host, port = parsed.hostname, parsed.port or 0
        uuid = parsed.username or ""
        params = parse_qs(parsed.query)
        label = unquote(parsed.fragment) if parsed.fragment else ""
        return ParsedServer(
            type="vless",
            address=host or "",
            port=port,
            security=params.get("security", [None])[0],
            meta={"uuid": uuid, "label": label, **{k: v[0] for k, v in params.items()}}  # pragma: allowlist secret
        )

    def _parse_vmess(self, line: str) -> ParsedServer:
        # vmess://base64(JSON)
        b64 = line[8:]
        try:
            decoded = base64.urlsafe_b64decode(b64 + '=' * (-len(b64) % 4)).decode('utf-8')
            import json
            data = json.loads(decoded)
            return ParsedServer(
                type="vmess",
                address=data.get("add", ""),
                port=int(data.get("port", 0)),
                security=data.get("security"),
                meta=data
            )
        except Exception:
            return ParsedServer(type="vmess", address="invalid", port=0, meta={"error": "base64/json decode failed"}) 