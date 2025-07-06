"""Pipeline coordination functionality for subscription manager."""

from typing import List, Tuple, Any, Optional

from ..models import PipelineContext, PipelineResult
from .error_handler import ErrorHandler


class PipelineCoordinator:
    """Coordinates pipeline stages for subscription processing.

    Manages the orchestration of middleware, policies, post-processing,
    and server selection stages of the subscription pipeline.
    """

    def __init__(
        self,
        middleware_chain=None,
        postprocessor=None,
        selector=None,
        error_handler: ErrorHandler = None
    ):
        """Initialize pipeline coordinator.

        Args:
            middleware_chain: Middleware chain for processing.
            postprocessor: Post-processor chain.
            selector: Server selector.
            error_handler: Optional error handler.
        """
        self.middleware_chain = middleware_chain
        self.postprocessor = postprocessor
        self.selector = selector
        self.error_handler = error_handler or ErrorHandler()

    def apply_policies(self, servers: List[Any], context: PipelineContext) -> List[Any]:
        """Apply policy rules to filter servers.

        Processes servers through registered policy plugins to apply
        filtering, transformation, and validation rules.

        Args:
            servers: List of parsed servers to process.
            context: Pipeline execution context.

        Returns:
            List of servers after policy application.
        """
        try:
            from ..policies.base import get_registered_policies
            policies = get_registered_policies()

            for policy_name, policy_class in policies.items():
                try:
                    policy_instance = policy_class()
                    servers = policy_instance.apply(servers, context)
                except Exception as e:
                    # Log policy error but continue processing
                    err = self.error_handler.create_internal_error(
                        f"policy_{policy_name}",
                        str(e),
                        {"policy": policy_name, "server_count": len(servers)}
                    )
                    self.error_handler.add_error_to_context(context, err)

            return servers

        except Exception as e:
            # If policy system fails, return servers unchanged
            err = self.error_handler.create_internal_error(
                "apply_policies",
                str(e),
                {"server_count": len(servers)}
            )
            self.error_handler.add_error_to_context(context, err)
            return servers

    def process_middleware(self, servers: List[Any], context: PipelineContext) -> Tuple[List[Any], bool]:
        """Process servers through middleware chain.

        Applies registered middleware transformations to enrich,
        filter, or modify server data.

        Args:
            servers: List of servers to process.
            context: Pipeline execution context.

        Returns:
            Tuple of (processed_servers, success_flag).
        """
        try:
            if not self.middleware_chain:
                return servers, True

            # Process through middleware chain
            processed_servers = self.middleware_chain.process(servers, context)
            return processed_servers, True

        except Exception as e:
            err = self.error_handler.create_internal_error(
                "middleware_processing",
                str(e),
                {"input_server_count": len(servers)}
            )
            self.error_handler.add_error_to_context(context, err)
            return servers, False

    def postprocess_and_select(
        self,
        servers: List[Any],
        user_routes: Optional[List[str]],
        exclusions: Optional[List[str]],
        mode: str
    ) -> Tuple[List[Any], bool]:
        """Post-process and select servers based on criteria.

        Applies post-processing transformations and then selects
        servers based on routing rules and exclusions.

        Args:
            servers: List of servers to process.
            user_routes: Optional list of user routing preferences.
            exclusions: Optional list of servers/tags to exclude.
            mode: Processing mode (strict/tolerant).

        Returns:
            Tuple of (selected_servers, success_flag).
        """
        try:
            # Apply post-processing
            if self.postprocessor:
                processed_servers = self.postprocessor.process(servers)
            else:
                processed_servers = servers

            # Apply server selection
            if self.selector:
                selected_servers = self.selector.select(
                    processed_servers,
                    user_routes,
                    exclusions,
                    mode
                )
            else:
                selected_servers = processed_servers

            return selected_servers, True

        except Exception:
            return servers, False

    def create_pipeline_result(
        self,
        servers: List[Any],
        context: PipelineContext,
        success: bool
    ) -> PipelineResult:
        """Create pipeline result object.

        Args:
            servers: Final processed servers.
            context: Pipeline execution context.
            success: Whether pipeline completed successfully.

        Returns:
            PipelineResult object with servers and context.
        """
        errors = context.metadata.get('errors', []) if hasattr(context, 'metadata') else []

        return PipelineResult(
            config=servers,
            context=context,
            errors=errors,
            success=success
        )

    def export_configuration(
        self,
        servers_result: PipelineResult,
        exclusions: Optional[List[str]] = None,
        user_routes: Optional[List[str]] = None,
        context: Optional[PipelineContext] = None,
        routing_plugin=None,
        export_manager=None
    ) -> PipelineResult:
        """Export final configuration using export manager.

        Args:
            servers_result: Result from get_servers pipeline.
            exclusions: Optional exclusion list.
            user_routes: Optional user routing preferences.
            context: Pipeline execution context.
            routing_plugin: Optional routing plugin.
            export_manager: Optional export manager instance.

        Returns:
            PipelineResult with exported configuration.
        """
        try:
            # Import here to avoid circular dependencies
            from sboxmgr.export.export_manager import ExportManager

            # Use provided ExportManager or create default
            mgr = export_manager or ExportManager(routing_plugin=routing_plugin)

            # Export configuration
            config = mgr.export(servers_result.config, exclusions, user_routes, context)

            return PipelineResult(
                config=config,
                context=context,
                errors=context.metadata.get('errors', []) if context else [],
                success=True
            )

        except Exception as e:
            if context:
                err = self.error_handler.create_internal_error(
                    "export_config",
                    str(e)
                )
                self.error_handler.add_error_to_context(context, err)
                errors = context.metadata.get('errors', [])
            else:
                errors = []

            return PipelineResult(
                config=None,
                context=context,
                errors=errors,
                success=False
            )
