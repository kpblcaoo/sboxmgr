import base64
import logging
import re
from typing import List
from urllib.parse import urlparse, parse_qs, unquote
from ..models import ParsedServer
from ..base_parser import BaseParser
from sboxmgr.utils.env import get_debug_level
from ..registry import register

logger = logging.getLogger(__name__)

@register("parser_uri_list")
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
                ss = self._parse_ss(line)
                if ss and ss.address != "invalid":
                    servers.append(ss)
                else:
                    if debug_level > 0:
                        logger.warning(f"Failed to parse ss:// line: {line}")
            elif line.startswith('vless://'):
                servers.append(self._parse_vless(line))
            elif line.startswith('vmess://'):
                servers.append(self._parse_vmess(line))
            elif line.startswith('trojan://'):
                trojan = self._parse_trojan(line)
                if trojan:
                    servers.append(trojan)
                else:
                    if debug_level > 0:
                        logger.warning(f"Failed to parse trojan:// line: {line}")
            else:
                if debug_level > 0:
                    logger.warning(f"Ignored line in uri list: {line}")
                servers.append(ParsedServer(type="unknown", address=line, port=0))
        return servers

    def _parse_ss(self, line: str) -> ParsedServer:
        # ss://[base64-encoded] или ss://method:password@host:port[#tag][?query]
        parsed = urlparse(line)
        uri = parsed.netloc + parsed.path
        tag = unquote(parsed.fragment) if parsed.fragment else ""
        query = parse_qs(parsed.query)
        debug_level = get_debug_level()
        # Попытка tolerant-декодирования как base64
        try:
            # Если есть @, base64 до @, иначе вся строка
            if '@' in uri:
                b64, after = uri.split('@', 1)
                try:
                    decoded = base64.urlsafe_b64decode(b64 + '=' * (-len(b64) % 4)).decode('utf-8')
                except Exception:
                    decoded = b64  # fallback: не base64, возможно plain
                method_pass = decoded
                host_port = after
            else:
                # Вся строка — base64 или plain
                try:
                    decoded = base64.urlsafe_b64decode(uri + '=' * (-len(uri) % 4)).decode('utf-8')
                except Exception:
                    decoded = uri  # fallback: не base64, возможно plain
                if '@' in decoded:
                    method_pass, host_port = decoded.split('@', 1)
                else:
                    if debug_level > 0:
                        logger.warning(f"ss:// no host in line: {line}")
                    return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "no host in ss://"})
            if ':' not in method_pass:
                if debug_level > 0:
                    logger.warning(f"ss:// parse failed (no colon in method:pass): {line}")
                return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "parse failed"})
            
            # host_port всегда содержит ':', так как мы проверили это выше
            method, password = method_pass.split(':', 1)
            host, port_str = host_port.split(':', 1)
            
            try:
                port = int(port_str)
            except ValueError:
                if debug_level > 0:
                    logger.warning(f"ss:// invalid port: {port_str} in line: {line}")
                return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "invalid port"})
            
            meta = {"password": password}  # pragma: allowlist secret
            if tag:
                meta["tag"] = tag
            for k, v in query.items():
                meta[k] = v[0] if v else ""
            return ParsedServer(
                type="ss",
                address=host,
                port=port,
                security=method,
                meta=meta
            )
        except Exception as e:
            # Если не base64 и не plain, пробуем tolerant-regex
            match = re.match(r'(?P<method>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)', uri)
            if match:
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
            if debug_level > 0:
                logger.warning(f"ss:// totally failed to parse: {line} ({e})")
            return ParsedServer(type="ss", address="invalid", port=0, meta={"error": "parse failed"})

    def _parse_trojan(self, line: str) -> ParsedServer:
        # trojan://password@host:port?params#tag
        parsed = urlparse(line)
        host, port = parsed.hostname, parsed.port or 0
        password = parsed.username or ""
        params = parse_qs(parsed.query)
        tag = unquote(parsed.fragment) if parsed.fragment else ""
        meta = {"tag": tag} if tag else {}
        meta["password"] = password
        for k, v in params.items():
            meta[k] = v[0] if v else ""
        return ParsedServer(
            type="trojan",
            address=host or "",
            port=port,
            security=None,
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