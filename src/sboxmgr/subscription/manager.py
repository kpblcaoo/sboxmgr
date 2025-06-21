from .models import SubscriptionSource, ParsedServer
from .registry import get_plugin, load_entry_points
from .fetchers import *  # noqa: F401, импортируем fetcher-плагины для регистрации
from typing import List, Optional
from src.sboxmgr.export.export_manager import ExportManager

def detect_parser(raw: bytes, source_type: str) -> Optional[object]:
    # Выбор парсера по source_type
    if source_type == "url_json":
        from .parsers.json_parser import JSONParser
        return JSONParser()
    elif source_type == "url_base64":
        from .parsers.base64_parser import Base64Parser
        return Base64Parser()
    elif source_type == "uri_list":
        from .parsers.uri_list_parser import URIListParser
        return URIListParser()
    # TODO: добавить эвристику по содержимому
    from .parsers.base64_parser import Base64Parser
    return Base64Parser()

class SubscriptionManager:
    def __init__(self, source: SubscriptionSource):
        load_entry_points()  # Подгружаем entry points, если есть
        fetcher_cls = get_plugin(source.source_type)
        if not fetcher_cls:
            # Fallback: попытка автоопределения типа (по расширению, mime и т.д.)
            # Пока просто ошибка
            raise ValueError(f"Unknown source_type: {source.source_type}")
        self.fetcher = fetcher_cls(source)

    def get_servers(self) -> List[ParsedServer]:
        raw = self.fetcher.fetch()
        parser = detect_parser(raw, self.fetcher.source.source_type)
        if not parser:
            raise ValueError("Could not detect parser for subscription data")
        return parser.parse(raw)

    def export_config(self, exclusions=None, user_routes=None, context=None, routing_plugin=None):
        exclusions = exclusions or []
        user_routes = user_routes or []
        context = context or {"mode": "default"}
        mgr = ExportManager(routing_plugin=routing_plugin)
        servers = self.get_servers()
        return mgr.export(servers, exclusions, user_routes, context) 