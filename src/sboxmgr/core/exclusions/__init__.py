"""Core exclusions package - modern exclusion management with DI support."""

from .interface import ExclusionManagerInterface
from .manager import ExclusionManager
from .models import ExclusionEntry, ExclusionList

# Clean API exports
__all__ = [
    "ExclusionManagerInterface",
    "ExclusionManager", 
    "ExclusionEntry",
    "ExclusionList",
]

# Convenience function for backward compatibility
def get_default_manager() -> ExclusionManager:
    """Get default ExclusionManager instance.
    
    Returns:
        Default ExclusionManager singleton
    """
    return ExclusionManager.default() 