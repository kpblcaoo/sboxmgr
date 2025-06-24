from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseParser(ABC):
    """Abstract base class for subscription parser plugins.
    
    This class provides the interface for parsing different subscription formats
    like base64, JSON, URI lists, etc. All parser plugins should inherit from
    this class and implement the parse method.
    
    Attributes:
        plugin_type: Plugin type identifier for auto-discovery and filtering.
    """
    
    plugin_type = "parser"
    
    @abstractmethod
    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Parse subscription data into a list of server configurations.
        
        Args:
            raw: Raw subscription data as bytes.
            
        Returns:
            List of ParsedServer objects containing parsed server configurations.
            
        Raises:
            ValueError: If the data format is invalid or cannot be parsed.
            NotImplementedError: If called directly on base class.
        """
        pass 