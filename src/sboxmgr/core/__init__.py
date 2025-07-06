"""Core sboxmgr architecture components.

This package provides the central orchestration layer and dependency
injection infrastructure for sboxmgr operations.
"""

from .orchestrator import Orchestrator, OrchestratorConfig, OrchestratorError
from .factory import ManagerFactory, create_default_exclusion_manager, create_default_export_manager
from .interfaces import (
    SubscriptionManagerInterface,
    ExportManagerInterface,
    ExclusionManagerInterface
)

__all__ = [
    'Orchestrator',
    'OrchestratorConfig',
    'OrchestratorError',
    'ManagerFactory',
    'create_default_exclusion_manager',
    'create_default_export_manager',
    'SubscriptionManagerInterface',
    'ExportManagerInterface',
    'ExclusionManagerInterface',
]

# Core modules will be imported as needed
