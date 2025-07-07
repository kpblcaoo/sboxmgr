"""Exclusion management module."""

from ..interfaces import ExclusionManagerInterface
from .manager import ExclusionManager
from .models import ExclusionEntry, ExclusionList

# Clean API exports
__all__ = [
    "ExclusionManager",
    "ExclusionManagerInterface",
    "ExclusionEntry",
    "ExclusionList",
]
