"""Enhanced middleware base classes for Phase 3 architecture.

This module defines the abstract base classes for middleware components that
process subscription data between pipeline stages. Middleware can transform,
filter, or enhance server data as it flows through the subscription
processing pipeline.

Implements Phase 3 architecture with profile integration and advanced features.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...configs.models import FullProfile
from ..models import ParsedServer, PipelineContext


class BaseMiddleware(ABC):
    """Enhanced base middleware interface for processing ParsedServer list.

    Phase 3 enhancements:
    - Profile-aware processing
    - Enhanced context support
    - Metadata collection
    - Error handling strategies
    - Conditional execution
    """

    middleware_type = "middleware"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize middleware with optional configuration.

        Args:
            config: Optional configuration dictionary for the middleware

        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

    @abstractmethod
    def process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> List[ParsedServer]:
        """Process servers through middleware transformation.

        Args:
            servers: List of ParsedServer objects to process
            context: Pipeline context containing processing state and configuration
            profile: Full profile configuration for profile-aware processing

        Returns:
            List[ParsedServer]: Processed servers after middleware transformation

        Raises:
            NotImplementedError: If called directly on base class

        """
        pass

    def can_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> bool:
        """Check if this middleware can process the given servers.

        Args:
            servers: List of servers to check
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            bool: True if this middleware can handle the servers

        """
        return self.enabled and len(servers) > 0

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this middleware.

        Returns:
            Dict containing middleware metadata

        """
        return {
            "name": self.__class__.__name__,
            "type": self.middleware_type,
            "enabled": self.enabled,
            "config": self.config,
        }


class ProfileAwareMiddleware(BaseMiddleware):
    """Base class for middleware that uses profile configuration.

    This class provides helper methods for extracting configuration
    from profiles and applying profile-based transformations.
    """

    def extract_middleware_config(
        self, profile: Optional[FullProfile]
    ) -> Dict[str, Any]:
        """Extract middleware configuration from profile.

        Args:
            profile: Full profile configuration

        Returns:
            Dict with middleware configuration

        """
        if not profile or "middleware" not in profile.metadata:
            return {}

        middleware_config = profile.metadata["middleware"]
        middleware_name = self.__class__.__name__.lower()

        return middleware_config.get(middleware_name, {})

    def should_process_server(
        self,
        server: ParsedServer,
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> bool:
        """Check if server should be processed by this middleware.

        Args:
            server: Server to check
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            bool: True if server should be processed

        """
        # Basic implementation - can be overridden
        return True


class ChainableMiddleware(ProfileAwareMiddleware):
    """Base class for middleware designed to work in chains.

    Provides additional methods for chain coordination and
    metadata passing between middleware components.
    """

    def pre_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> None:
        """Called before main processing. Override for setup logic.

        Args:
            servers: List of servers to be processed
            context: Pipeline context
            profile: Full profile configuration

        """
        pass

    def post_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> None:
        """Called after main processing. Override for cleanup logic.

        Args:
            servers: List of processed servers
            context: Pipeline context
            profile: Full profile configuration

        """
        pass

    def process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> List[ParsedServer]:
        """Process servers with pre/post hooks.

        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            List of processed servers

        """
        self.pre_process(servers, context, profile)
        result = self._do_process(servers, context, profile)
        self.post_process(result, context, profile)
        return result

    @abstractmethod
    def _do_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> List[ParsedServer]:
        """Main processing logic. Override this method.

        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            List of processed servers

        """
        pass


class ConditionalMiddleware(ChainableMiddleware):
    """Base class for middleware with conditional execution logic.

    Provides methods for determining when middleware should execute
    based on various conditions like server count, profile settings,
    context state, etc.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize conditional middleware.

        Args:
            config: Configuration dictionary with conditional settings

        """
        super().__init__(config)
        self.conditions = self.config.get("conditions", {})
        self.min_servers = self.conditions.get("min_servers", 0)
        self.max_servers = self.conditions.get("max_servers", float("inf"))
        self.required_metadata = self.conditions.get("required_metadata", [])
        self.execution_mode = self.conditions.get("execution_mode", "always")

    def can_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> bool:
        """Enhanced conditional processing check.

        Args:
            servers: List of servers to check
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            bool: True if middleware should execute

        """
        if not super().can_process(servers, context, profile):
            return False

        # Check server count conditions
        server_count = len(servers)
        if server_count < self.min_servers or server_count > self.max_servers:
            return False

        # Check required metadata
        for metadata_key in self.required_metadata:
            if not any(metadata_key in server.meta for server in servers):
                return False

        # Check execution mode
        if self.execution_mode == "never":
            return False
        elif self.execution_mode == "profile_only" and not profile:
            return False
        elif self.execution_mode == "debug_only" and context.debug_level == 0:
            return False

        return True


class TransformMiddleware(ConditionalMiddleware):
    """Base class for middleware that transforms server data.

    Provides common patterns for server data transformation including
    field mapping, value conversion, and metadata enrichment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize transform middleware.

        Args:
            config: Configuration with transformation settings

        """
        super().__init__(config)
        self.field_mappings = self.config.get("field_mappings", {})
        self.value_transformers = self.config.get("value_transformers", {})
        self.metadata_enrichers = self.config.get("metadata_enrichers", [])

    def transform_server(
        self,
        server: ParsedServer,
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> ParsedServer:
        """Transform a single server.

        Args:
            server: Server to transform
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            Transformed server

        """
        # Apply field mappings
        for source_field, target_field in self.field_mappings.items():
            if hasattr(server, source_field):
                value = getattr(server, source_field)
                setattr(server, target_field, value)

        # Apply value transformers
        for field, transformer_name in self.value_transformers.items():
            if hasattr(server, field):
                value = getattr(server, field)
                transformed_value = self._apply_transformer(transformer_name, value)
                setattr(server, field, transformed_value)

        # Apply metadata enrichers
        for enricher_config in self.metadata_enrichers:
            self._apply_metadata_enricher(server, enricher_config, context, profile)

        return server

    def _apply_transformer(self, transformer_name: str, value: Any) -> Any:
        """Apply value transformer.

        Args:
            transformer_name: Name of transformer to apply
            value: Value to transform

        Returns:
            Transformed value

        """
        # Basic transformers - can be extended
        if transformer_name == "uppercase":
            return str(value).upper() if value else value
        elif transformer_name == "lowercase":
            return str(value).lower() if value else value
        elif transformer_name == "strip":
            return str(value).strip() if value else value
        else:
            return value

    def _apply_metadata_enricher(
        self,
        server: ParsedServer,
        enricher_config: Dict[str, Any],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> None:
        """Apply metadata enricher to server.

        Args:
            server: Server to enrich
            enricher_config: Enricher configuration
            context: Pipeline context
            profile: Full profile configuration

        """
        enricher_type = enricher_config.get("type")

        if enricher_type == "timestamp":
            import time

            server.meta["processed_at"] = time.time()
        elif enricher_type == "trace_id":
            server.meta["trace_id"] = context.trace_id
        elif enricher_type == "source":
            server.meta["source"] = context.source
        # Add more enrichers as needed
