from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List, Optional

class BaseSelector(ABC):
    """Abstract base class for server selection strategies.
    
    This class defines the interface for selecting servers from a list based
    on various criteria like user routes, exclusions, and selection modes.
    """
    
    @abstractmethod
    def select(self, servers: List[ParsedServer], user_routes: Optional[List[str]] = None, exclusions: Optional[List[str]] = None, mode: Optional[str] = None) -> List[ParsedServer]:
        """Select servers based on the specified criteria.
        
        Args:
            servers: List of parsed servers to select from.
            user_routes: Optional list of route tags to include.
            exclusions: Optional list of route tags to exclude.
            mode: Optional selection mode (e.g., 'random', 'urltest').
            
        Returns:
            List of selected ParsedServer objects.
            
        Raises:
            NotImplementedError: If called directly on base class.
        """
        pass

class DefaultSelector(BaseSelector):
    """Default server selector that applies basic filtering rules.
    
    This selector filters servers based on exclusion lists and user routes.
    It implements a simple tag-based filtering mechanism.
    """
    
    def select(self, servers: List[ParsedServer], user_routes: Optional[List[str]] = None, exclusions: Optional[List[str]] = None, mode: Optional[str] = None) -> List[ParsedServer]:
        """Select servers using default filtering logic.
        
        Applies exclusion filtering first, then user route filtering if specified.
        Supports wildcard '*' in user routes to include all non-excluded servers.
        
        Args:
            servers: List of parsed servers to select from.
            user_routes: Optional list of route tags to include. Supports '*' wildcard.
            exclusions: Optional list of route tags to exclude.
            mode: Optional selection mode (currently unused, reserved for future extensions).
            
        Returns:
            List of filtered ParsedServer objects matching the selection criteria.
        """
        user_routes = user_routes or []
        exclusions = exclusions or []
        # Фильтрация по exclusions (по тегу)
        filtered = [s for s in servers if not (getattr(s, 'meta', {}).get('tag') in exclusions)]
        # Если user_routes указаны, фильтруем только по ним (по тегу)
        if user_routes:
            filtered = [s for s in filtered if getattr(s, 'meta', {}).get('tag') in user_routes or '*' in user_routes]
        # mode пока не используется, но можно расширить
        return filtered 