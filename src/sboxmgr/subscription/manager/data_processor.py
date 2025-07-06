"""Data processing functionality for subscription manager."""

from typing import Tuple, List, Any

from ..models import PipelineContext
from .error_handler import ErrorHandler
from .parser_detector import detect_parser


class DataProcessor:
    """Handles data processing stages of the subscription pipeline.
    
    Manages fetching, parsing, and validation of subscription data
    with comprehensive error handling and debugging support.
    """
    
    def __init__(self, fetcher, error_handler: ErrorHandler = None):
        """Initialize data processor.
        
        Args:
            fetcher: Subscription data fetcher instance.
            error_handler: Optional error handler (creates default if None).
        """
        self.fetcher = fetcher
        self.error_handler = error_handler or ErrorHandler()
    
    def fetch_and_validate_raw(self, context: PipelineContext) -> Tuple[bytes, bool]:
        """Fetch and validate raw subscription data.
        
        Handles the initial data fetching and raw validation stages
        of the subscription processing pipeline.
        
        Args:
            context: Pipeline execution context for logging and error tracking.
            
        Returns:
            Tuple of (raw_data, success_flag). If success_flag is False,
            appropriate errors will be added to context.metadata['errors'].
        """
        try:
            # Log User-Agent if debug enabled
            self._log_user_agent(context)
            
            # Fetch raw data
            raw = self.fetcher.fetch()
            
            # Debug logging
            self._log_fetch_result(context, raw)
            
            # Validate raw data
            return self._validate_raw_data(raw, context)
            
        except Exception as e:
            err = self.error_handler.create_fetch_error(
                str(e),
                {"source_type": self.fetcher.source.source_type}
            )
            self.error_handler.add_error_to_context(context, err)
            return b'', False
    
    def parse_servers(self, raw_data: bytes, context: PipelineContext) -> Tuple[List[Any], bool]:
        """Parse raw subscription data into server objects.
        
        Detects appropriate parser and converts raw data into
        structured server configuration objects.
        
        Args:
            raw_data: Raw subscription data bytes.
            context: Pipeline execution context.
            
        Returns:
            Tuple of (parsed_servers, success_flag).
        """
        try:
            # Detect and get parser
            parser = detect_parser(raw_data, self.fetcher.source.source_type)
            if not parser:
                err = self.error_handler.create_parse_error(
                    "No suitable parser found for data format",
                    {"source_type": self.fetcher.source.source_type}
                )
                self.error_handler.add_error_to_context(context, err)
                return [], False
            
            # Parse servers
            servers = parser.parse(raw_data)
            
            # Debug logging
            self._log_parse_result(context, servers, parser)
            
            return servers, True
            
        except Exception as e:
            err = self.error_handler.create_parse_error(
                str(e),
                {"source_type": self.fetcher.source.source_type}
            )
            self.error_handler.add_error_to_context(context, err)
            return [], False
    
    def validate_parsed_servers(self, servers: List[Any], context: PipelineContext) -> Tuple[List[Any], bool]:
        """Validate parsed server configurations.
        
        Applies parsed validation rules to ensure server configurations
        meet minimum requirements for further processing.
        
        Args:
            servers: List of parsed server objects to validate.
            context: Pipeline execution context.
            
        Returns:
            Tuple of (validated_servers, success_flag).
        """
        try:
            debug_level = getattr(context, 'debug_level', 0)
            
            # Get parsed validator
            validator = self._get_parsed_validator()
            if not validator:
                return servers, True  # No validator available
            
            # Run validation
            parsed_result = validator.validate(servers, context)
            
            # Debug logging
            if debug_level >= 2:
                print(f"[DEBUG] ParsedValidator valid_servers: {getattr(parsed_result, 'valid_servers', None)} errors: {parsed_result.errors}")
            
            # Handle validation results based on mode
            return self._handle_validation_results(servers, parsed_result, context)
            
        except Exception as e:
            err = self.error_handler.create_validation_error(
                "parsed_validate",
                str(e),
                {"server_count": len(servers)}
            )
            self.error_handler.add_error_to_context(context, err)
            return servers, False
    
    def _log_user_agent(self, context: PipelineContext) -> None:
        """Log User-Agent information if debug enabled."""
        debug_level = getattr(context, 'debug_level', 0)
        if debug_level >= 1:
            ua = getattr(self.fetcher.source, 'user_agent', None)
            if ua == "":
                print("[fetcher] Using User-Agent: [none]")
            elif ua:
                print(f"[fetcher] Using User-Agent: {ua}")
            else:
                print("[fetcher] Using User-Agent: ClashMeta/1.0")
    
    def _log_fetch_result(self, context: PipelineContext, raw: bytes) -> None:
        """Log fetch result if debug enabled."""
        debug_level = getattr(context, 'debug_level', 0)
        if debug_level >= 2:
            print(f"[debug] Fetched {len(raw)} bytes. First 200 bytes: {raw[:200]!r}")
    
    def _log_parse_result(self, context: PipelineContext, servers: List[Any], parser) -> None:
        """Log parse result if debug enabled."""
        debug_level = getattr(context, 'debug_level', 0)
        if debug_level >= 1:
            print(f"[debug] Parser {parser.__class__.__name__} returned {len(servers)} servers")
    
    def _validate_raw_data(self, raw: bytes, context: PipelineContext) -> Tuple[bytes, bool]:
        """Validate raw subscription data."""
        # Raw validation
        from ..validators.base import RAW_VALIDATOR_REGISTRY
        validator_cls = RAW_VALIDATOR_REGISTRY.get("noop")
        if not validator_cls:
            return raw, True
        
        validator = validator_cls()
        result = validator.validate(raw, context)
        
        if not result.valid:
            err = self.error_handler.create_validation_error(
                "raw_validate",
                "; ".join(result.errors),
                {"source_type": self.fetcher.source.source_type}
            )
            self.error_handler.add_error_to_context(context, err)
            return raw, False
        
        return raw, True
    
    def _get_parsed_validator(self):
        """Get parsed validator instance."""
        from ..validators.base import PARSED_VALIDATOR_REGISTRY
        parsed_validator_cls = PARSED_VALIDATOR_REGISTRY.get("required_fields")
        if not parsed_validator_cls:
            return None
        return parsed_validator_cls()
    
    def _handle_validation_results(self, servers: List[Any], parsed_result, context: PipelineContext) -> Tuple[List[Any], bool]:
        """Handle validation results based on pipeline mode."""
        # Add validation errors to context
        for error in parsed_result.errors:
            err = self.error_handler.create_validation_error(
                "parsed_validate",
                error,
                {"total_servers": len(servers)}
            )
            self.error_handler.add_error_to_context(context, err)
        
        # Return results based on mode
        if context.mode == 'strict':
            # In strict mode, return all servers (including invalid) with errors
            if servers:
                return servers, True
            else:
                return servers, False
        else:
            # In tolerant mode, return only valid servers
            validated_servers = getattr(parsed_result, 'valid_servers', servers)
            return validated_servers, bool(validated_servers)
