"""Base middleware interface for subscription processing pipeline.

This module defines the abstract base class for middleware components that
process subscription data between pipeline stages. Middleware can transform,
filter, or enhance server data as it flows through the subscription
processing pipeline.
"""
from abc import ABC, abstractmethod
from typing import List
from .models import ParsedServer, PipelineContext
import hashlib
import warnings

class BaseMiddleware(ABC):
    """Базовый интерфейс middleware для обработки списка ParsedServer.

    Args:
        servers (List[ParsedServer]): Список серверов.
        context (PipelineContext): Контекст пайплайна.

    Returns:
        List[ParsedServer]: Результат обработки.
    """
    @abstractmethod
    def process(self, servers: List[ParsedServer], context: PipelineContext) -> List[ParsedServer]:
        """Process servers through middleware transformation.
        
        Args:
            servers: List of ParsedServer objects to process.
            context: Pipeline context containing processing state and configuration.
            
        Returns:
            List[ParsedServer]: Processed servers after middleware transformation.
            
        Raises:
            NotImplementedError: If called directly on base class.
        """

class MiddlewareChain(BaseMiddleware):
    """Цепочка middleware, вызываемых по порядку для обработки списка ParsedServer."""
    def __init__(self, middlewares: list):
        self.middlewares = middlewares
    def process(self, servers: List[ParsedServer], context: PipelineContext) -> List[ParsedServer]:
        """Process servers through the middleware chain sequentially.
        
        Args:
            servers: List of ParsedServer objects to process.
            context: Pipeline context containing processing state.
            
        Returns:
            List[ParsedServer]: Servers after processing through all middleware.
        """
        for mw in self.middlewares:
            servers = mw.process(servers, context)
        return servers

class LoggingMiddleware(BaseMiddleware):
    """Debug middleware for logging server processing information.
    
    This middleware logs processing stage information including server count
    and content hash for debugging and audit purposes.
    """
    
    def __init__(self, stage_name: str = "middleware"):
        self.stage_name = stage_name
        
    def process(self, servers: List[ParsedServer], context: PipelineContext) -> List[ParsedServer]:
        """Process servers with debug logging information.
        
        Args:
            servers: List of ParsedServer objects to process.
            context: Pipeline context containing debug configuration.
            
        Returns:
            List[ParsedServer]: Original servers (unchanged by debug middleware).
        """
        debug_level = getattr(context, 'debug_level', 0)
        if debug_level > 0:
            data = str([(s.type, s.address, s.port) for s in servers]).encode()
            h = hashlib.sha256(data).hexdigest()[:16]  # Truncate for readability
            print(f"[DEBUG][{self.stage_name}] servers: {len(servers)}, sha256: {h}")
        return servers

# === Sandbox/audit registration ===
MIDDLEWARE_REGISTRY = {}

def register_middleware(cls):
    """Регистрирует middleware с sandbox/audit: проверка интерфейса, логирование."""
    if not issubclass(cls, BaseMiddleware):
        raise TypeError(f"{cls.__name__} must inherit from BaseMiddleware")
    if not cls.__doc__ or 'Google' not in (cls.__doc__ or ''):
        warnings.warn(f"{cls.__name__} has no Google-style docstring (recommended)")
    MIDDLEWARE_REGISTRY[cls.__name__] = cls
    print(f"[AUDIT] Registered middleware: {cls.__name__}")
    return cls

class TagFilterMiddleware(BaseMiddleware):
    """Фильтрует серверы по тегу из context.tag_filters (список тегов)."""
    def process(self, servers: List[ParsedServer], context: PipelineContext) -> List[ParsedServer]:
        tags = getattr(context, 'tag_filters', None)
        # Базовая валидация user input (SEC-MW-05)
        if tags is not None:
            if not isinstance(tags, list):
                raise ValueError("tag_filters must be a list of strings")
            for tag in tags:
                if not isinstance(tag, str) or len(tag) > 64 or not tag.isprintable():
                    raise ValueError(f"Invalid tag in tag_filters: {tag!r}")
        if not tags:
            return servers
        return [s for s in servers if getattr(s, 'meta', {}).get('tag') in tags]

class EnrichMiddleware(BaseMiddleware):
    """Обогащает ParsedServer: добавляет country='??' в meta (stub).
    
    WARNING: Не реализует внешний lookup! Если потребуется enrichment через внешние сервисы — обязательно реализовать таймаут, sandbox, SEC-аудит (см. SEC-MW-04).
    """
    def process(self, servers: List[ParsedServer], context: PipelineContext) -> List[ParsedServer]:
        for s in servers:
            if not hasattr(s, 'meta') or s.meta is None:
                s.meta = {}
            s.meta['country'] = '??'
        return servers 