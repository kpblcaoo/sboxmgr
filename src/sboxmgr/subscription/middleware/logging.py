"""Logging middleware implementation for Phase 3 architecture.

This module provides middleware for logging server processing events,
performance metrics, and debugging information throughout the pipeline.
Integrates with the existing logging system and supports profile-based
logging configuration.

Implements Phase 3 architecture with profile integration.
"""

import time
from typing import List, Optional, Dict, Any
from .base import ChainableMiddleware
from ..models import ParsedServer, PipelineContext
from ...profiles.models import FullProfile
from ...logging.core import get_logger


class LoggingMiddleware(ChainableMiddleware):
    """Logging middleware with profile integration and performance tracking.
    
    Logs server processing events, performance metrics, and debugging
    information throughout the pipeline. Supports different log levels
    and filtering based on profile configuration.
    
    Configuration options:
    - log_level: Minimum log level ('debug', 'info', 'warning', 'error')
    - log_server_details: Whether to log individual server details
    - log_performance: Whether to log performance metrics
    - log_errors_only: Only log when errors occur
    - max_servers_logged: Maximum number of servers to log details for
    - include_metadata: Whether to include server metadata in logs
    - log_format: Format for log messages ('simple', 'detailed', 'json')
    
    Example:
        middleware = LoggingMiddleware({
            'log_level': 'info',
            'log_server_details': True,
            'log_performance': True,
            'max_servers_logged': 10
        })
        processed_servers = middleware.process(servers, context, profile)
    """
    
    middleware_type = "logging"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize logging middleware.
        
        Args:
            config: Configuration dictionary for logging options
        """
        super().__init__(config)
        self.log_level = self.config.get('log_level', 'info')
        self.log_server_details = self.config.get('log_server_details', False)
        self.log_performance = self.config.get('log_performance', True)
        self.log_errors_only = self.config.get('log_errors_only', False)
        self.max_servers_logged = self.config.get('max_servers_logged', 5)
        self.include_metadata = self.config.get('include_metadata', False)
        self.log_format = self.config.get('log_format', 'simple')
        
        self.logger = get_logger(__name__)
        self._start_time = 0.0
    
    def pre_process(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        profile: Optional[FullProfile] = None
    ) -> None:
        """Log processing start information.
        
        Args:
            servers: List of servers to be processed
            context: Pipeline context
            profile: Full profile configuration
        """
        self._start_time = time.time()
        
        # Extract logging configuration from profile
        log_config = self._extract_log_config(profile)
        
        if not self.log_errors_only:
            if self.log_format == 'json':
                self.logger.info("Pipeline processing started", extra={
                    'event': 'pipeline_start',
                    'trace_id': context.trace_id,
                    'server_count': len(servers),
                    'source': context.source,
                    'profile_id': profile.id if profile else None
                })
            else:
                self.logger.info(
                    f"Processing {len(servers)} servers "
                    f"(trace_id: {context.trace_id}, source: {context.source})"
                )
            
            # Log server details if enabled
            if self.log_server_details and log_config.get('log_server_details', self.log_server_details):
                self._log_server_details(servers, context, "input")
    
    def post_process(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        profile: Optional[FullProfile] = None
    ) -> None:
        """Log processing completion information.
        
        Args:
            servers: List of processed servers
            context: Pipeline context
            profile: Full profile configuration
        """
        duration = time.time() - self._start_time
        
        # Extract logging configuration from profile
        log_config = self._extract_log_config(profile)
        
        if not self.log_errors_only:
            if self.log_format == 'json':
                self.logger.info("Pipeline processing completed", extra={
                    'event': 'pipeline_complete',
                    'trace_id': context.trace_id,
                    'input_count': context.metadata.get('input_server_count', 0),
                    'output_count': len(servers),
                    'duration_seconds': round(duration, 3),
                    'servers_per_second': round(len(servers) / duration, 2) if duration > 0 else 0
                })
            else:
                self.logger.info(
                    f"Processing completed: {len(servers)} servers processed "
                    f"in {duration:.3f}s ({len(servers)/duration:.2f} servers/sec)"
                )
            
            # Log performance metrics if enabled
            if self.log_performance and log_config.get('log_performance', self.log_performance):
                self._log_performance_metrics(servers, context, duration)
            
            # Log server details if enabled
            if self.log_server_details and log_config.get('log_server_details', self.log_server_details):
                self._log_server_details(servers, context, "output")
    
    def _do_process(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Main processing logic - pass through with logging.
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of servers (unchanged)
        """
        # Store input count for post-processing metrics
        context.metadata['input_server_count'] = len(servers)
        
        # Log any errors in server data
        self._log_server_errors(servers, context)
        
        # Pass through servers unchanged
        return servers
    
    def _extract_log_config(self, profile: Optional[FullProfile]) -> Dict[str, Any]:
        """Extract logging configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            Dictionary with logging configuration
        """
        log_config = {
            'log_level': self.log_level,
            'log_server_details': self.log_server_details,
            'log_performance': self.log_performance,
            'log_errors_only': self.log_errors_only,
            'max_servers_logged': self.max_servers_logged,
            'include_metadata': self.include_metadata,
            'log_format': self.log_format
        }
        
        if not profile:
            return log_config
        
        # Check for logging-specific metadata in profile
        if 'logging' in profile.metadata:
            logging_meta = profile.metadata['logging']
            for key in log_config:
                if key in logging_meta:
                    log_config[key] = logging_meta[key]
        
        # Check agent configuration for logging settings
        if profile.agent:
            log_config['log_level'] = profile.agent.log_level
        
        return log_config
    
    def _log_server_details(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        stage: str
    ) -> None:
        """Log details about servers.
        
        Args:
            servers: List of servers to log
            context: Pipeline context
            stage: Processing stage ('input' or 'output')
        """
        servers_to_log = servers[:self.max_servers_logged]
        
        for i, server in enumerate(servers_to_log):
            if self.log_format == 'json':
                server_data = {
                    'event': f'server_{stage}',
                    'trace_id': context.trace_id,
                    'server_index': i,
                    'type': server.type,
                    'address': server.address,
                    'port': server.port,
                    'tag': server.tag
                }
                
                if self.include_metadata:
                    server_data['metadata'] = server.meta
                
                self.logger.debug(f"Server {stage} details", extra=server_data)
            else:
                metadata_str = f" (meta: {server.meta})" if self.include_metadata else ""
                self.logger.debug(
                    f"Server {i+1}: {server.type}://{server.address}:{server.port} "
                    f"[{server.tag or 'no-tag'}]{metadata_str}"
                )
        
        if len(servers) > self.max_servers_logged:
            self.logger.debug(f"... and {len(servers) - self.max_servers_logged} more servers")
    
    def _log_performance_metrics(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        duration: float
    ) -> None:
        """Log performance metrics.
        
        Args:
            servers: List of processed servers
            context: Pipeline context
            duration: Processing duration in seconds
        """
        metrics = {
            'total_servers': len(servers),
            'duration_seconds': round(duration, 3),
            'servers_per_second': round(len(servers) / duration, 2) if duration > 0 else 0,
            'memory_usage_mb': self._get_memory_usage(),
            'trace_id': context.trace_id
        }
        
        # Count servers by type
        server_types = {}
        for server in servers:
            server_types[server.type] = server_types.get(server.type, 0) + 1
        metrics['server_types'] = server_types
        
        if self.log_format == 'json':
            self.logger.info("Performance metrics", extra={
                'event': 'performance_metrics',
                **metrics
            })
        else:
            self.logger.info(
                f"Performance: {metrics['total_servers']} servers, "
                f"{metrics['duration_seconds']}s, "
                f"{metrics['servers_per_second']} servers/sec, "
                f"{metrics['memory_usage_mb']}MB memory"
            )
    
    def _log_server_errors(self, servers: List[ParsedServer], context: PipelineContext) -> None:
        """Log any errors found in server data.
        
        Args:
            servers: List of servers to check
            context: Pipeline context
        """
        error_count = 0
        
        for i, server in enumerate(servers):
            errors = []
            
            # Check for common server data issues
            if not server.address:
                errors.append("missing address")
            if not server.port or server.port <= 0:
                errors.append("invalid port")
            if not server.type:
                errors.append("missing type")
            
            # Check for error metadata
            if 'error' in server.meta:
                errors.append(f"metadata error: {server.meta['error']}")
            
            if errors:
                error_count += 1
                if self.log_format == 'json':
                    self.logger.warning("Server validation errors", extra={
                        'event': 'server_errors',
                        'trace_id': context.trace_id,
                        'server_index': i,
                        'server_address': server.address,
                        'server_port': server.port,
                        'errors': errors
                    })
                else:
                    self.logger.warning(
                        f"Server {i+1} ({server.address}:{server.port}) has errors: {', '.join(errors)}"
                    )
        
        if error_count > 0:
            self.logger.warning(f"Found {error_count} servers with errors out of {len(servers)} total")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            return 0.0
    
    def can_process(
        self, 
        servers: List[ParsedServer], 
        context: PipelineContext,
        profile: Optional[FullProfile] = None
    ) -> bool:
        """Check if logging middleware should process.
        
        Args:
            servers: List of servers
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            bool: True if logging is enabled
        """
        if not super().can_process(servers, context, profile):
            return False
        
        # Check if logging is disabled in profile
        if profile and 'logging' in profile.metadata:
            logging_config = profile.metadata['logging']
            if not logging_config.get('enabled', True):
                return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about logging middleware.
        
        Returns:
            Dict containing middleware metadata
        """
        metadata = super().get_metadata()
        metadata.update({
            'log_level': self.log_level,
            'log_server_details': self.log_server_details,
            'log_performance': self.log_performance,
            'log_format': self.log_format,
            'max_servers_logged': self.max_servers_logged
        })
        return metadata 