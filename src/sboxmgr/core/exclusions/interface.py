"""Interface for ExclusionManager implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict


class ExclusionManagerInterface(ABC):
    """Interface for exclusion management implementations.
    
    Allows for different exclusion strategies:
    - File-based exclusions (default)
    - GeoIP-based exclusions (plugin)
    - Tag-based exclusions (plugin)
    - Database-based exclusions (plugin)
    """
    
    @abstractmethod
    def add(self, server_id: str, name: str = None, reason: str = None) -> bool:
        """Add server to exclusions.
        
        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            reason: Reason for exclusion
            
        Returns:
            True if added, False if already existed
        """
        pass
    
    @abstractmethod
    def remove(self, server_id: str) -> bool:
        """Remove server from exclusions.
        
        Args:
            server_id: Unique server identifier
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    @abstractmethod
    def contains(self, server_id: str) -> bool:
        """Check if server is excluded.
        
        Args:
            server_id: Unique server identifier
            
        Returns:
            True if excluded, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict]:
        """List all exclusions.
        
        Returns:
            List of exclusion dictionaries with id, name, reason, timestamp
        """
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """Clear all exclusions.
        
        Returns:
            Number of exclusions cleared
        """
        pass
    
    @abstractmethod
    def filter_servers(self, servers: List) -> List:
        """Filter servers by removing excluded ones.
        
        Args:
            servers: List of ParsedServer objects
            
        Returns:
            Filtered list without excluded servers
        """
        pass
    
    @abstractmethod
    def get_excluded_ids(self) -> set:
        """Get set of excluded server IDs for fast lookup.
        
        Returns:
            Set of excluded server IDs
        """
        pass 