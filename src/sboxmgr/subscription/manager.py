from .models import SubscriptionSource, ParsedServer, PipelineContext, PipelineResult
from .registry import get_plugin, load_entry_points
from .fetchers import *  # noqa: F401, импортируем fetcher-плагины для регистрации
from typing import List, Optional
from sboxmgr.export.export_manager import ExportManager
from .base_selector import DefaultSelector
from .postprocessor_base import DedupPostProcessor, PostProcessorChain
from .errors import PipelineError, ErrorType
from datetime import datetime, timezone
from .validators.base import RAW_VALIDATOR_REGISTRY, ValidationResult
from .middleware_base import MiddlewareChain
import functools
import threading

def detect_parser(raw: bytes, source_type: str) -> Optional[object]:
    text = raw[:2000].decode('utf-8', errors='ignore').lstrip()
    # 1. Пробуем tolerant JSON
    from .parsers.json_parser import TolerantJSONParser, JSONParser
    try:
        parser = TolerantJSONParser()
        data = parser._strip_comments_and_validate(text)[0]
        import json
        json.loads(data)
        return parser
    except Exception:
        pass
    # 2. Пробуем Clash YAML
    if text.startswith(("mixed-port:", "proxies:", "proxy-groups:", "proxy-providers:")) or 'proxies:' in text:
        from .parsers.clash_parser import ClashParser
        return ClashParser()
    # 3. Пробуем base64 (если строка похожа на base64)
    import base64
    import re
    b64_re = re.compile(r'^[A-Za-z0-9+/=\s]+$')
    if b64_re.match(text) and len(text.strip()) > 100:
        try:
            decoded = base64.b64decode(text.strip() + '=' * (-len(text.strip()) % 4))
            decoded_text = decoded.decode('utf-8', errors='ignore')
            if any(proto in decoded_text for proto in ("vless://", "vmess://", "trojan://", "ss://")):
                from .parsers.base64_parser import Base64Parser
                return Base64Parser()
        except Exception:
            pass
    # 4. Пробуем plain URI list
    lines = text.splitlines()
    if any(l.strip().startswith(("vless://", "vmess://", "trojan://", "ss://")) for l in lines):
        from .parsers.uri_list_parser import URIListParser
        return URIListParser()
    # fallback
    from .parsers.base64_parser import Base64Parser
    return Base64Parser()

class SubscriptionManager:
    _cache_lock = threading.Lock()
    _get_servers_cache = {}

    def __init__(self, source: SubscriptionSource, detect_parser=None, postprocessor_chain=None, middleware_chain=None):
        """Инициализация менеджера подписок.

        Args:
            source (SubscriptionSource): Описание источника подписки.
            detect_parser (callable, optional): Функция для auto-detect парсера.
            postprocessor_chain (BasePostProcessor, optional): Цепочка postprocessor-плагинов (по умолчанию DedupPostProcessor).
            middleware_chain (BaseMiddleware, optional): Цепочка middleware (по умолчанию пустая).
        """
        load_entry_points()  # Подгружаем entry points, если есть
        fetcher_cls = get_plugin(source.source_type)
        if not fetcher_cls:
            # Fallback: попытка автоопределения типа (по расширению, mime и т.д.)
            # Пока просто ошибка
            raise ValueError(f"Unknown source_type: {source.source_type}")
        self.fetcher = fetcher_cls(source)
        from .postprocessor_base import PostProcessorChain, DedupPostProcessor
        if postprocessor_chain is not None:
            self.postprocessor = postprocessor_chain
        else:
            self.postprocessor = PostProcessorChain([DedupPostProcessor()])
        from .middleware_base import MiddlewareChain
        if middleware_chain is not None:
            self.middleware_chain = middleware_chain
        else:
            self.middleware_chain = MiddlewareChain([])
        self.selector = DefaultSelector()
        if detect_parser is None:
            from .manager import detect_parser as default_detect_parser
            self.detect_parser = default_detect_parser
        else:
            self.detect_parser = detect_parser

    def get_servers(self, user_routes=None, exclusions=None, mode=None, context: PipelineContext = None, force_reload: bool = False) -> PipelineResult:
        """Получить список ParsedServer из подписки с учётом фильтрации, fail-tolerance и edge-cases.

        Args:
            user_routes (list, optional): Список пользовательских маршрутов (тегов) для фильтрации серверов.
            exclusions (list, optional): Список исключаемых маршрутов (тегов).
            mode (str, optional): Режим работы пайплайна ('strict' — fail-fast, 'tolerant' — partial success).
            context (PipelineContext, optional): Контекст выполнения пайплайна (trace_id, debug_level и др.).
            force_reload (bool, optional): Принудительно сбросить кеш и заново получить результат.

        Returns:
            PipelineResult: Результат выполнения пайплайна, включающий список ParsedServer (config), контекст, ошибки и флаг успеха.

        Raises:
            None: Все ошибки аккумулируются в errors PipelineResult, критические ошибки приводят к success=False.
        """
        context = context or PipelineContext()
        if 'errors' not in context.metadata:
            context.metadata['errors'] = []
        # Формируем ключ кеша по всем влияющим параметрам
        key = (
            str(self.fetcher.source.url),
            getattr(self.fetcher.source, 'user_agent', None),
            str(getattr(self.fetcher.source, 'headers', None)),
            str(getattr(context, 'tag_filters', None)),
            str(mode),
        )
        if force_reload:
            with self._cache_lock:
                self._get_servers_cache.pop(key, None)
        with self._cache_lock:
            if key in self._get_servers_cache:
                result = self._get_servers_cache[key]
                # Не возвращаем кеш, если он содержит ошибку
                if result.success:
                    return result
        try:
            raw = self.fetcher.fetch()
            # Удаляем все отладочные print, кроме debug_level > 0
            debug_level = getattr(context, 'debug_level', 0)
            if debug_level > 0:
                print(f"[debug] Fetched {len(raw)} bytes. First 200 bytes: {raw[:200]!r}")
            validator_cls = RAW_VALIDATOR_REGISTRY.get("noop")
            validator = validator_cls()
            result = validator.validate(raw, context)
            if not result.valid:
                err = PipelineError(
                    type=ErrorType.VALIDATION,
                    stage="raw_validate",
                    message="; ".join(result.errors),
                    context={"source_type": self.fetcher.source.source_type},
                    timestamp=datetime.now(timezone.utc)
                )
                context.metadata['errors'].append(err)
                if context.mode == 'strict':
                    return PipelineResult(config=None, context=context, errors=context.metadata['errors'], success=False)
                else:
                    return PipelineResult(config=[], context=context, errors=context.metadata['errors'], success=False)
            parser = self.detect_parser(raw, self.fetcher.source.source_type)
            if debug_level > 0:
                print(f"[debug] Selected parser: {getattr(parser, '__class__', type(parser)).__name__}")
            if not parser:
                err = PipelineError(
                    type=ErrorType.PARSE,
                    stage="detect_parser",
                    message="Could not detect parser for subscription data",
                    context={"source_type": self.fetcher.source.source_type},
                    timestamp=datetime.now(timezone.utc)
                )
                context.metadata['errors'].append(err)
                if context.mode == 'strict':
                    return PipelineResult(config=None, context=context, errors=context.metadata['errors'], success=False)
                else:
                    return PipelineResult(config=[], context=context, errors=context.metadata['errors'], success=False)
            servers = parser.parse(raw)
            servers = self.middleware_chain.process(servers, context)
            if debug_level > 0:
                print(f"[debug] servers after middleware: {servers[:3]}{' ...' if len(servers) > 3 else ''}")
            servers = self.postprocessor.process(servers)
            servers = self.selector.select(servers, user_routes=user_routes, exclusions=exclusions, mode=mode)
            result = PipelineResult(config=servers, context=context, errors=context.metadata['errors'], success=True)
            with self._cache_lock:
                self._get_servers_cache[key] = result
            return result
        except Exception as e:
            err = PipelineError(
                type=ErrorType.INTERNAL,
                stage="get_servers",
                message=str(e),
                context={},
                timestamp=datetime.now(timezone.utc)
            )
            context.metadata['errors'].append(err)
            return PipelineResult(config=None, context=context, errors=context.metadata['errors'], success=False)

    def export_config(self, exclusions=None, user_routes=None, context: PipelineContext = None, routing_plugin=None) -> PipelineResult:
        """Экспортировать подписку в итоговый конфиг (например, sing-box JSON) с учётом фильтрации, роутинга и fail-tolerance.

        Args:
            exclusions (list, optional): Список исключаемых маршрутов (тегов).
            user_routes (list, optional): Список пользовательских маршрутов (тегов).
            context (PipelineContext, optional): Контекст выполнения пайплайна (trace_id, debug_level и др.).
            routing_plugin (object, optional): Плагин для генерации маршрутов (по умолчанию — стандартный).

        Returns:
            PipelineResult: Результат экспорта, включающий итоговый конфиг (config), контекст, ошибки и флаг успеха.

        Raises:
            None: Все ошибки аккумулируются в errors PipelineResult, критические ошибки приводят к success=False.
        """
        exclusions = exclusions or []
        user_routes = user_routes or []
        context = context or PipelineContext()
        if 'errors' not in context.metadata:
            context.metadata['errors'] = []
        servers_result = self.get_servers(user_routes=user_routes, exclusions=exclusions, mode=context.mode, context=context)
        if not servers_result.success:
            return PipelineResult(config=None, context=servers_result.context, errors=servers_result.errors, success=False)
        mgr = ExportManager(routing_plugin=routing_plugin)
        try:
            config = mgr.export(servers_result.config, exclusions, user_routes, context)
            return PipelineResult(config=config, context=context, errors=context.metadata['errors'], success=True)
        except Exception as e:
            err = PipelineError(
                type=ErrorType.INTERNAL,
                stage="export_config",
                message=str(e),
                context={},
                timestamp=datetime.now(timezone.utc)
            )
            context.metadata['errors'].append(err)
            return PipelineResult(config=None, context=context, errors=context.metadata['errors'], success=False) 