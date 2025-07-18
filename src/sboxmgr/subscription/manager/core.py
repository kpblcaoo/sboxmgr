"""Core subscription manager implementation."""

from typing import Optional

from ..base_selector import DefaultSelector

# Import fetchers and parsers for plugin registration
from ..fetchers import *  # noqa: F401
from ..middleware_base import MiddlewareChain
from ..models import PipelineContext, PipelineResult, SubscriptionSource
from ..parsers import *  # noqa: F401
from ..postprocessor_base import DedupPostProcessor, PostProcessorChain
from ..registry import get_plugin, load_entry_points
from .cache import CacheManager
from .data_processor import DataProcessor
from .error_handler import ErrorHandler
from .pipeline_coordinator import PipelineCoordinator


class SubscriptionManager:
    """Manages subscription data processing pipeline.

    This class orchestrates the complete subscription processing workflow
    including fetching, validation, parsing, middleware processing, and
    server selection. It provides a unified interface for handling various
    subscription formats and sources with comprehensive error handling
    and caching support.

    The pipeline stages are:
    1. Fetch raw data from source
    2. Validate raw data
    3. Parse into server configurations
    4. Apply middleware transformations
    5. Post-process and deduplicate
    6. Select servers based on criteria

    Attributes:
        fetcher: Plugin for fetching subscription data.
        cache_manager: Cache management for expensive operations.
        error_handler: Centralized error handling.
        data_processor: Data processing pipeline stages.
        pipeline_coordinator: Pipeline coordination and orchestration.

    """

    def __init__(
        self,
        source: SubscriptionSource,
        detect_parser=None,
        postprocessor_chain=None,
        middleware_chain=None,
    ):
        """Initialize subscription manager with configuration.

        Args:
            source: Subscription source configuration.
            detect_parser: Optional custom parser detection function.
            postprocessor_chain: Optional custom post-processor chain.
            middleware_chain: Optional custom middleware chain.

        Raises:
            ValueError: If source_type is unknown or unsupported.

        """
        # Load plugins
        load_entry_points()

        # Initialize fetcher
        fetcher_cls = get_plugin(source.source_type)
        if not fetcher_cls:
            raise ValueError(f"Unknown source_type: {source.source_type}")

        self.fetcher = fetcher_cls(source)

        # Initialize components
        self.cache_manager = CacheManager()
        self.error_handler = ErrorHandler()
        self.data_processor = DataProcessor(self.fetcher, self.error_handler)

        # Setup pipeline components
        self.postprocessor = postprocessor_chain or PostProcessorChain(
            [DedupPostProcessor()]
        )
        self.middleware_chain = middleware_chain or MiddlewareChain([])
        self.selector = DefaultSelector()

        # Initialize pipeline coordinator
        self.pipeline_coordinator = PipelineCoordinator(
            middleware_chain=self.middleware_chain,
            postprocessor=self.postprocessor,
            selector=self.selector,
            error_handler=self.error_handler,
        )

        # Setup parser detection
        self.detect_parser = detect_parser or detect_parser

    def get_servers(
        self,
        user_routes: Optional[list[str]] = None,
        exclusions: Optional[list[str]] = None,
        mode: Optional[str] = None,
        context: Optional[PipelineContext] = None,
        force_reload: bool = False,
    ) -> PipelineResult:
        """Execute subscription processing pipeline to get servers.

        Processes subscription data through the complete pipeline including
        fetching, parsing, validation, middleware processing, and selection.

        Args:
            user_routes: Optional list of user-specified routes to include.
            exclusions: Optional list of servers/tags to exclude.
            mode: Processing mode ('strict' or 'tolerant'). Defaults to 'tolerant'.
            context: Optional pipeline context. Creates default if None.
            force_reload: Whether to bypass cache and force fresh data fetch.

        Returns:
            PipelineResult containing processed servers, context, errors, and success status.

        """
        # Setup defaults
        user_routes = user_routes or []
        exclusions = exclusions or []
        mode = mode or "tolerant"

        # Create or update context
        if context is None:
            context = PipelineContext(mode=mode)
        else:
            context.mode = mode

        # Initialize context metadata
        if not hasattr(context, "metadata"):
            context.metadata = {}
        if "errors" not in context.metadata:
            context.metadata["errors"] = []

        # Check cache unless force_reload
        if not force_reload:
            cache_key = self.cache_manager.create_cache_key(
                mode, context, self.fetcher.source
            )
            cached_result = self.cache_manager.get_cached_result(cache_key)
            if cached_result:
                return cached_result

        # Execute pipeline stages
        result = self._execute_pipeline(user_routes, exclusions, mode, context)

        # Cache successful results
        if result.success and not force_reload:
            cache_key = self.cache_manager.create_cache_key(
                mode, context, self.fetcher.source
            )
            self.cache_manager.set_cached_result(cache_key, result)

        return result

    def export_config(
        self,
        exclusions: Optional[list[str]] = None,
        user_routes: Optional[list[str]] = None,
        context: Optional[PipelineContext] = None,
        routing_plugin=None,
        export_manager=None,
    ) -> PipelineResult:
        """Export subscription configuration using export manager.

        Processes subscription data and exports it in the desired format
        using the configured export manager and routing plugin.

        Args:
            exclusions: Optional list of servers/tags to exclude.
            user_routes: Optional list of user routing preferences.
            context: Optional pipeline context.
            routing_plugin: Optional routing plugin for export.
            export_manager: Optional export manager instance.

        Returns:
            PipelineResult containing exported configuration.

        """
        # Get servers first
        servers_result = self.get_servers(
            user_routes=user_routes, exclusions=exclusions, context=context
        )

        # If get_servers failed, return the failure
        if not servers_result.success:
            return servers_result

        # Export configuration
        return self.pipeline_coordinator.export_configuration(
            servers_result=servers_result,
            exclusions=exclusions,
            user_routes=user_routes,
            context=context,
            routing_plugin=routing_plugin,
            export_manager=export_manager,
        )

    def _execute_pipeline(
        self,
        user_routes: list[str],
        exclusions: list[str],
        mode: str,
        context: PipelineContext,
    ) -> PipelineResult:
        """Execute the complete subscription processing pipeline.

        Args:
            user_routes: User routing preferences.
            exclusions: Exclusion list.
            mode: Processing mode.
            context: Pipeline context.

        Returns:
            PipelineResult with processed servers.

        """
        # Stage 1: Fetch and validate raw data
        raw_data, fetch_success = self.data_processor.fetch_and_validate_raw(context)
        if not fetch_success:
            return self.pipeline_coordinator.create_pipeline_result([], context, False)

        # Stage 2: Parse servers
        servers, parse_success = self.data_processor.parse_servers(raw_data, context)
        if not parse_success:
            return self.pipeline_coordinator.create_pipeline_result([], context, False)

        # Stage 3: Validate parsed servers
        (
            validated_servers,
            validation_success,
        ) = self.data_processor.validate_parsed_servers(servers, context)
        if not validation_success and mode != "strict":
            return self.pipeline_coordinator.create_pipeline_result([], context, False)

        # Stage 4: Apply policies
        policy_servers = self.pipeline_coordinator.apply_policies(
            validated_servers, context
        )

        # Stage 5: Process middleware
        (
            middleware_servers,
            middleware_success,
        ) = self.pipeline_coordinator.process_middleware(policy_servers, context)

        # Stage 6: Post-process and select
        (
            final_servers,
            selection_success,
        ) = self.pipeline_coordinator.postprocess_and_select(
            middleware_servers, user_routes, exclusions, mode
        )

        # Determine overall success
        overall_success = (
            fetch_success
            and parse_success
            and (validation_success or mode == "strict")
            and middleware_success
            and selection_success
        )

        return self.pipeline_coordinator.create_pipeline_result(
            final_servers, context, overall_success
        )
