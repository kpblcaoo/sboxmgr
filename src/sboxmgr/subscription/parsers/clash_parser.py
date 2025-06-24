import yaml
from ..models import ParsedServer
from ..base_parser import BaseParser
from ..registry import register

@register("clash")
class ClashParser(BaseParser):
    def parse(self, raw: bytes):
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