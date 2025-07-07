"""Error handling functionality for subscription manager."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..errors import ErrorType, PipelineError


class ErrorHandler:
    """Handles error creation and management for subscription processing.

    Provides centralized error handling with standardized error creation,
    logging, and context management for the subscription pipeline.
    """

    def __init__(self):
        """Initialize error handler."""
        pass

    def create_pipeline_error(
        self,
        error_type: ErrorType,
        stage: str,
        message: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> PipelineError:
        """Create standardized pipeline error.

        Centralizes pipeline error creation with consistent structure
        and timestamp handling.

        Args:
            error_type: Type of error that occurred.
            stage: Pipeline stage where error occurred.
            message: Human-readable error description.
            context_data: Optional additional context information.

        Returns:
            Formatted PipelineError object.
        """
        return PipelineError(
            type=error_type,
            stage=stage,
            message=message,
            context=context_data or {},
            timestamp=datetime.now(timezone.utc),
        )

    def create_fetch_error(
        self, message: str, context_data: Optional[Dict[str, Any]] = None
    ) -> PipelineError:
        """Create fetch stage error.

        Args:
            message: Error description.
            context_data: Optional context information.

        Returns:
            Fetch error object.
        """
        return self.create_pipeline_error(
            ErrorType.FETCH, "fetch", message, context_data
        )

    def create_validation_error(
        self, stage: str, message: str, context_data: Optional[Dict[str, Any]] = None
    ) -> PipelineError:
        """Create validation stage error.

        Args:
            stage: Validation stage name.
            message: Error description.
            context_data: Optional context information.

        Returns:
            Validation error object.
        """
        return self.create_pipeline_error(
            ErrorType.VALIDATION, stage, message, context_data
        )

    def create_parse_error(
        self, message: str, context_data: Optional[Dict[str, Any]] = None
    ) -> PipelineError:
        """Create parse stage error.

        Args:
            message: Error description.
            context_data: Optional context information.

        Returns:
            Parse error object.
        """
        return self.create_pipeline_error(
            ErrorType.PARSE, "parse", message, context_data
        )

    def create_internal_error(
        self, stage: str, message: str, context_data: Optional[Dict[str, Any]] = None
    ) -> PipelineError:
        """Create internal stage error.

        Args:
            stage: Processing stage name.
            message: Error description.
            context_data: Optional context information.

        Returns:
            Internal error object.
        """
        return self.create_pipeline_error(
            ErrorType.INTERNAL, stage, message, context_data
        )

    def add_error_to_context(self, context, error: PipelineError) -> None:
        """Add error to pipeline context.

        Args:
            context: Pipeline context to add error to.
            error: Error to add.
        """
        if not hasattr(context, "metadata"):
            context.metadata = {}
        if "errors" not in context.metadata:
            context.metadata["errors"] = []

        context.metadata["errors"].append(error)

    def has_errors(self, context) -> bool:
        """Check if context has any errors.

        Args:
            context: Pipeline context to check.

        Returns:
            True if context has errors, False otherwise.
        """
        return (
            hasattr(context, "metadata")
            and context.metadata
            and context.metadata.get("errors")
        )

    def get_error_count(self, context) -> int:
        """Get number of errors in context.

        Args:
            context: Pipeline context to check.

        Returns:
            Number of errors in context.
        """
        if not self.has_errors(context):
            return 0
        return len(context.metadata["errors"])
