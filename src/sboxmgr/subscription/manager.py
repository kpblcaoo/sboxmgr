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

import threading

def detect_parser(raw: bytes, source_type: str) -> Optional[object]:
    """Detect the appropriate parser for subscription data.
    
    Attempts to identify the correct parser based on data format analysis
    and source type hints. Uses various heuristics including content
    inspection, format detection, and fallback strategies.
    
    Args:
        raw: Raw subscription data to analyze.
        source_type: Hint about the expected source type.
        
    Returns:
        Parser instance capable of handling the data format, or None if
        no suitable parser could be determined.
        
    Note:
        Falls back to Base64Parser if no specific parser is detected,
        as this handles the most common subscription format.
    """
    text = raw[:2000].decode('utf-8', errors='ignore').lstrip()
    # 1. Пробуем tolerant JSON
    from .parsers.json_parser import TolerantJSONParser
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
    """Manages subscription data processing pipeline.
    
    This class orchestrates the complete subscription processing workflow
    including fetching, validation, parsing, middleware processing, and
    server selection. It provides a unified interface for handling various
    subscription formats and sources with comprehensive error handling
    and caching support.
    
    The pipeline stages are:
    1. Fetch raw data from source
    2. Validate raw data
    3. Parse into server configurations  
    4. Apply middleware transformations
    5. Post-process and deduplicate
    6. Select servers based on criteria
    
    Attributes:
        fetcher: Plugin for fetching subscription data.
        postprocessor: Chain of post-processing plugins.
        middleware_chain: Chain of middleware plugins.
        selector: Server selection strategy.
        detect_parser: Function for auto-detecting parsers.
    """
    
    _cache_lock = threading.Lock()
    _get_servers_cache = {}

    def __init__(self, source: SubscriptionSource, detect_parser=None, postprocessor_chain=None, middleware_chain=None):
        """Initialize subscription manager with configuration.

        Args:
            source: Subscription source configuration.
            detect_parser: Optional custom parser detection function.
            postprocessor_chain: Optional custom post-processor chain.
            middleware_chain: Optional custom middleware chain.
            
        Raises:
            ValueError: If source_type is unknown or unsupported.
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
        """Retrieve and process servers from subscription with comprehensive pipeline.

        Executes the complete subscription processing pipeline including fetching,
        validation, parsing, middleware processing, and server selection. Supports
        caching, error tolerance, and detailed debugging information.

        Args:
            user_routes: Optional list of route tags to include in selection.
            exclusions: Optional list of route tags to exclude from selection.
            mode: Pipeline execution mode ('strict' for fail-fast, 'tolerant' for partial success).
            context: Optional pipeline execution context for tracing and debugging.
            force_reload: Whether to bypass cache and force fresh data retrieval.

        Returns:
            PipelineResult containing:
            - config: List of ParsedServer objects or None on critical failure
            - context: Execution context with trace information
            - errors: List of PipelineError objects for any issues encountered
            - success: Boolean indicating overall pipeline success
            
        Note:
            In 'tolerant' mode, partial failures may still return success=True with
            warnings in the errors list. In 'strict' mode, any error causes failure.
            
            Results are cached based on source URL, headers, filters, and mode to
            improve performance for repeated requests.
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
            # Логируем User-Agent на уровне 1
            debug_level = getattr(context, 'debug_level', 0)
            if debug_level >= 1:
                ua = getattr(self.fetcher.source, 'user_agent', None)
                if ua:
                    print(f"[fetcher] Using User-Agent: {ua}")
                else:
                    print(f"[fetcher] Using User-Agent: [default]")
            raw = self.fetcher.fetch()
            # Отладочные print в зависимости от debug_level
            if debug_level >= 2:
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
            if debug_level >= 2:
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
            if debug_level >= 1:
                print(f"[info] Parsed {len(servers)} servers from subscription")
            # === ParsedValidator ===
            from sboxmgr.subscription.validators.base import PARSED_VALIDATOR_REGISTRY
            parsed_validator_cls = PARSED_VALIDATOR_REGISTRY.get("required_fields")
            if parsed_validator_cls:
                parsed_validator = parsed_validator_cls()
                parsed_result = parsed_validator.validate(servers, context)
                if debug_level >= 2:
                    print(f"[DEBUG] ParsedValidator valid_servers: {getattr(parsed_result, 'valid_servers', None)} errors: {parsed_result.errors}")
                servers = getattr(parsed_result, 'valid_servers', servers)
                if debug_level >= 2:
                    print(f"[DEBUG] servers after validation: {servers}")
                if not servers:
                    if debug_level >= 2:
                        print(f"[DEBUG] No valid servers after validation, returning empty config and success=False")
                    err = PipelineError(
                        type=ErrorType.VALIDATION,
                        stage="parsed_validate",
                        message="; ".join(parsed_result.errors),
                        context={"source_type": self.fetcher.source.source_type},
                        timestamp=datetime.now(timezone.utc)
                    )
                    context.metadata['errors'].append(err)
                    return PipelineResult(config=[], context=context, errors=context.metadata['errors'], success=False)
                if parsed_result.errors:
                    err = PipelineError(
                        type=ErrorType.VALIDATION,
                        stage="parsed_validate",
                        message="; ".join(parsed_result.errors),
                        context={"source_type": self.fetcher.source.source_type},
                        timestamp=datetime.now(timezone.utc)
                    )
                    context.metadata['errors'].append(err)
            # === End ParsedValidator ===
            servers = self.middleware_chain.process(servers, context)
            if debug_level >= 2:
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

    def export_config(self, exclusions=None, user_routes=None, context: PipelineContext = None, routing_plugin=None, export_manager: Optional[ExportManager] = None, skip_version_check: bool = False) -> PipelineResult:
        """Export subscription to final configuration format.

        Processes the subscription through the complete pipeline and exports
        the result to a target configuration format (e.g., sing-box JSON)
        with routing rules, filtering, and format-specific optimizations.

        Args:
            exclusions: Optional list of route tags to exclude.
            user_routes: Optional list of route tags to include.
            context: Optional pipeline execution context.
            routing_plugin: Optional custom routing plugin for rule generation.
            export_manager: Optional export manager with target format configuration.
            skip_version_check: Whether to skip version compatibility checks.

        Returns:
            PipelineResult containing:
            - config: Final configuration in target format or None on failure
            - context: Execution context with processing details
            - errors: List of any errors encountered during export
            - success: Boolean indicating export success
            
        Raises:
            None: All errors are captured in the PipelineResult.errors list.
            
        Note:
            This method combines get_servers() with format-specific export logic.
            The export format is determined by the export_manager configuration.
        """
        exclusions = exclusions or []
        user_routes = user_routes or []
        context = context or PipelineContext()
        if 'errors' not in context.metadata:
            context.metadata['errors'] = []
        servers_result = self.get_servers(user_routes=user_routes, exclusions=exclusions, mode=context.mode, context=context)
        if not servers_result.success:
            return PipelineResult(config=None, context=servers_result.context, errors=servers_result.errors, success=False)
        
        # Используем переданный ExportManager или создаём дефолтный
        mgr = export_manager or ExportManager(routing_plugin=routing_plugin)
        try:
            config = mgr.export(servers_result.config, exclusions, user_routes, context, skip_version_check=skip_version_check)
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