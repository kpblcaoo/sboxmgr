from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List, Optional

class BaseSelector(ABC):
    @abstractmethod
    def select(self, servers: List[ParsedServer], user_routes: Optional[List[str]] = None, exclusions: Optional[List[str]] = None, mode: Optional[str] = None) -> List[ParsedServer]:
        """Выбрать серверы по заданной политике (например, urltest, random, manual)."""
        pass

class DefaultSelector(BaseSelector):
    def select(self, servers: List[ParsedServer], user_routes: Optional[List[str]] = None, exclusions: Optional[List[str]] = None, mode: Optional[str] = None) -> List[ParsedServer]:
        user_routes = user_routes or []
        exclusions = exclusions or []
        # Фильтрация по exclusions (по тегу)
        filtered = [s for s in servers if not (getattr(s, 'meta', {}).get('tag') in exclusions)]
        # Если user_routes указаны, фильтруем только по ним (по тегу)
        if user_routes:
            filtered = [s for s in filtered if getattr(s, 'meta', {}).get('tag') in user_routes or '*' in user_routes]
        # mode пока не используется, но можно расширить
        return filtered 