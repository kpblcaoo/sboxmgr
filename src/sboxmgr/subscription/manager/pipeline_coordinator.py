"""Pipeline coordination functionality for subscription manager."""

from typing import Any, Optional

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
        error_handler: ErrorHandler = None,
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

    def apply_policies(self, servers: list[Any], context: PipelineContext) -> list[Any]:
        """Apply policy rules to filter servers.

        Processes servers through registered policy plugins to apply
        filtering, transformation, and validation rules.

        Args:
            servers: List of parsed servers to process.
            context: Pipeline execution context.

        Returns:
            List of servers after policy application.
        """
        import logging

        logger = logging.getLogger("sboxmgr.subscription.manager.pipeline_coordinator")

        # Check if policies should be skipped
        if getattr(context, "skip_policies", False):
            logger.debug(
                "[Pipeline] Skipping policy application due to skip_policies flag"
            )
            return servers

        try:
            from sboxmgr.policies import PolicyContext, policy_registry

            policies = policy_registry.policies
            logger.debug(
                f"[Pipeline] Applying {len(policies)} policies to {len(servers)} servers"
            )

            fail_tolerant = getattr(context, "fail_tolerant", False)

            for policy in policies:
                try:
                    logger.debug(f"[Pipeline] Applying policy: {policy.name}")
                    # Apply policy to each server individually
                    filtered_servers = []
                    for server in servers:
                        pol_ctx = PolicyContext(
                            server=server,
                            profile=getattr(context, "profile", None),
                            user=getattr(context, "user", None),
                            env=getattr(context, "env", {}),
                        )
                        result = policy.evaluate(pol_ctx)
                        logger.debug(
                            f"[Pipeline] Server {getattr(server, 'address', 'unknown')}: {result.allowed} - {result.reason}"
                        )
                        if result.allowed:
                            filtered_servers.append(server)
                    servers = filtered_servers
                    logger.debug(
                        f"[Pipeline] After policy {policy.name}: {len(servers)} servers remain"
                    )
                except Exception as e:
                    logger.error(f"[Pipeline] Policy {policy.name} error: {e}")
                    err = self.error_handler.create_internal_error(
                        f"policy_{policy.name}",
                        str(e),
                        {"policy": policy.name, "server_count": len(servers)},
                    )
                    self.error_handler.add_error_to_context(context, err)
                    if fail_tolerant:
                        context.metadata["policy_error"] = str(e)
                        if not hasattr(context, "flags"):
                            context.flags = []
                        context.flags.append("policy_error")
                        return servers
                    else:
                        raise
            return servers
        except Exception as e:
            logger.critical(f"[Pipeline] Policy application failed: {e}")
            fail_tolerant = getattr(context, "fail_tolerant", False)
            if fail_tolerant:
                context.metadata["policy_error"] = str(e)
                if not hasattr(context, "flags"):
                    context.flags = []
                context.flags.append("policy_error")
                return servers
            else:
                raise

    def process_middleware(
        self, servers: list[Any], context: PipelineContext
    ) -> tuple[list[Any], bool]:
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
                "middleware_processing", str(e), {"input_server_count": len(servers)}
            )
            self.error_handler.add_error_to_context(context, err)
            return servers, False

    def postprocess_and_select(
        self,
        servers: list[Any],
        user_routes: Optional[list[str]],
        exclusions: Optional[list[str]],
        mode: str,
    ) -> tuple[list[Any], bool]:
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
                    processed_servers, user_routes, exclusions, mode
                )
            else:
                selected_servers = processed_servers

            return selected_servers, True

        except Exception:
            return servers, False

    def create_pipeline_result(
        self, servers: list[Any], context: PipelineContext, success: bool
    ) -> PipelineResult:
        """Create pipeline result object.

        Args:
            servers: Final processed servers.
            context: Pipeline execution context.
            success: Whether pipeline completed successfully.

        Returns:
            PipelineResult object with servers and context.
        """
        errors = (
            context.metadata.get("errors", []) if hasattr(context, "metadata") else []
        )
        return PipelineResult(
            config=servers, context=context, errors=errors, success=success
        )

    def export_configuration(
        self,
        servers_result: PipelineResult,
        exclusions: Optional[list[str]] = None,
        user_routes: Optional[list[str]] = None,
        context: Optional[PipelineContext] = None,
        routing_plugin=None,
        export_manager=None,
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
                errors=context.metadata.get("errors", []) if context else [],
                success=True,
            )

        except Exception as e:
            if context:
                err = self.error_handler.create_internal_error("export_config", str(e))
                self.error_handler.add_error_to_context(context, err)
                errors = context.metadata.get("errors", [])
            else:
                errors = []

            return PipelineResult(
                config=None, context=context, errors=errors, success=False
            )
