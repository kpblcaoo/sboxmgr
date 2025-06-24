from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseExporter(ABC):
    """Abstract base class for configuration exporters.
    
    This class provides the interface for exporting parsed server configurations
    to various formats like sing-box JSON, Clash YAML, v2ray config, etc.
    All exporter plugins should inherit from this class and implement the export method.
    
    Attributes:
        plugin_type: Plugin type identifier for auto-discovery and filtering.
    """
    
    plugin_type = "exporter"

    @abstractmethod
    def export(self, servers: List[ParsedServer]) -> str:
        """Export a list of parsed servers to a configuration string.
        
        Args:
            servers: List of ParsedServer objects to export.
            
        Returns:
            Configuration string in the target format (JSON, YAML, etc.).
            
        Raises:
            ValueError: If server data is invalid or cannot be exported.
            NotImplementedError: If called directly on base class.
        """
        pass

# TODO: реализовать sing-box exporter и расширяемую архитектуру для других форматов 