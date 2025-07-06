"""Factory functions for creating default manager instances.

This module provides factory functions for creating default implementations
of manager interfaces used by the Orchestrator. This enables proper
dependency injection while maintaining backward compatibility.
"""

from typing import Optional
from .interfaces import (
    SubscriptionManagerInterface,
    ExportManagerInterface,
    ExclusionManagerInterface
)


def create_default_subscription_manager() -> SubscriptionManagerInterface:
    """Create default subscription manager implementation.
    
    Note: This factory creates a subscription manager without a source,
    which is expected behavior since sources are created per-request
    in the Orchestrator.
    
    Returns:
        Default subscription manager instance.

    """
    # Import here to avoid circular imports
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource
    
    # Create a dummy source for the interface compliance
    # In practice, Orchestrator creates managers with real sources
    dummy_source = SubscriptionSource(url="dummy://", source_type="url_base64")
    return SubscriptionManager(dummy_source)


def create_default_export_manager() -> ExportManagerInterface:
    """Create default export manager implementation.
    
    Returns:
        Default export manager instance with standard configuration.

    """
    from sboxmgr.export.export_manager import ExportManager
    return ExportManager()


def create_default_exclusion_manager() -> ExclusionManagerInterface:
    """Create default exclusion manager implementation.
    
    Returns:
        Default exclusion manager instance using standard file storage.

    """
    from sboxmgr.core.exclusions.manager import ExclusionManager
    return ExclusionManager.default()


class ManagerFactory:
    """Factory class for creating and configuring manager instances.
    
    Provides a centralized way to create manager instances with
    custom configurations and dependency injection support.
    """
    
    @staticmethod
    def create_subscription_manager(source, **kwargs) -> SubscriptionManagerInterface:
        """Create subscription manager with specific source.
        
        Args:
            source: SubscriptionSource instance.
            **kwargs: Additional configuration parameters.
            
        Returns:
            Configured subscription manager instance.

        """
        from sboxmgr.subscription.manager import SubscriptionManager
        return SubscriptionManager(source, **kwargs)
    
    @staticmethod
    def create_export_manager(export_format: str = "singbox", **kwargs) -> ExportManagerInterface:
        """Create export manager with specific format.
        
        Args:
            export_format: Target export format.
            **kwargs: Additional configuration parameters.
            
        Returns:
            Configured export manager instance.

        """
        from sboxmgr.export.export_manager import ExportManager
        return ExportManager(export_format=export_format, **kwargs)
    
    @staticmethod
    def create_exclusion_manager(file_path: Optional[str] = None, **kwargs) -> ExclusionManagerInterface:
        """Create exclusion manager with specific file path.
        
        Args:
            file_path: Custom path for exclusions file.
            **kwargs: Additional configuration parameters.
            
        Returns:
            Configured exclusion manager instance.

        """
        from sboxmgr.core.exclusions.manager import ExclusionManager
        if file_path:
            from pathlib import Path
            return ExclusionManager(file_path=Path(file_path), **kwargs)
        else:
            return ExclusionManager.default()
