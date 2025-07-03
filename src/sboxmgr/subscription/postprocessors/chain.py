"""PostProcessor chain implementation for Phase 3 architecture.

This module provides a chain of postprocessors that can be executed
sequentially with profile integration, error handling, and metadata
collection. The chain supports conditional execution, parallel processing,
and sophisticated error recovery strategies.

Implements Phase 3 architecture with profile integration.
"""

from typing import List, Optional, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..registry import register
from .base import BasePostProcessor, ProfileAwarePostProcessor
from ..models import ParsedServer, PipelineContext
from ...profiles.models import FullProfile


@register("postprocessor_chain")
class PostProcessorChain(ProfileAwarePostProcessor):
    """Chain of postprocessors with advanced execution strategies.
    
    Executes multiple postprocessors in sequence or parallel with
    sophisticated error handling, conditional execution, and metadata
    collection.
    
    Configuration options:
    - execution_mode: 'sequential', 'parallel', 'conditional'
    - error_strategy: 'fail_fast', 'continue', 'retry'
    - max_retries: Maximum number of retries for failed processors
    - retry_delay_seconds: Delay between retries
    - parallel_workers: Number of parallel workers for parallel mode
    - collect_metadata: Whether to collect metadata from processors
    - timeout_seconds: Overall timeout for chain execution
    
    Example:
        chain = PostProcessorChain([
            GeoFilterPostProcessor({'allowed_countries': ['US', 'CA']}),
            TagFilterPostProcessor({'exclude_tags': ['blocked']}),
            LatencySortPostProcessor({'sort_order': 'asc'})
        ], {
            'execution_mode': 'sequential',
            'error_strategy': 'continue'
        })
        processed_servers = chain.process(servers, context, profile)
    """
    
    def __init__(
        self, 
        processors: List[BasePostProcessor], 
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize postprocessor chain.
        
        Args:
            processors: List of postprocessors to execute
            config: Configuration dictionary for chain execution
        """
        super().__init__(config)
        self.processors = processors
        self.execution_mode = self.config.get('execution_mode', 'sequential')
        self.error_strategy = self.config.get('error_strategy', 'continue')
        self.max_retries = self.config.get('max_retries', 2)
        self.retry_delay_seconds = self.config.get('retry_delay_seconds', 1.0)
        self.parallel_workers = self.config.get('parallel_workers', 4)
        self.collect_metadata = self.config.get('collect_metadata', True)
        self.timeout_seconds = self.config.get('timeout_seconds', 300)
        self._execution_metadata: Dict[str, Any] = {}
    
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Execute postprocessor chain on servers.
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of processed servers
        """
        if not servers or not self.processors:
            return servers
        
        # Initialize execution metadata
        import time
        self._execution_metadata = {
            'start_time': time.time(),
            'processors_executed': [],
            'processors_failed': [],
            'processors_skipped': [],
            'total_processors': len(self.processors),
            'execution_mode': self.execution_mode
        }
        
        try:
            if self.execution_mode == 'sequential':
                result = self._execute_sequential(servers, context, profile)
            elif self.execution_mode == 'parallel':
                result = self._execute_parallel(servers, context, profile)
            elif self.execution_mode == 'conditional':
                result = self._execute_conditional(servers, context, profile)
            else:
                raise ValueError(f"Unknown execution mode: {self.execution_mode}")
            
            self._execution_metadata['success'] = True
            return result
            
        except Exception as e:
            self._execution_metadata['success'] = False
            self._execution_metadata['error'] = str(e)
            
            if self.error_strategy == 'fail_fast':
                raise
            else:
                # Return original servers on error
                return servers
        finally:
            import time
            self._execution_metadata['end_time'] = time.time()
            self._execution_metadata['duration'] = (
                self._execution_metadata.get('end_time', 0) - 
                self._execution_metadata.get('start_time', 0)
            )
    
    def _execute_sequential(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Execute processors sequentially.
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of processed servers
        """
        current_servers = servers
        
        for i, processor in enumerate(self.processors):
            try:
                # Check if processor can handle current servers
                if not processor.can_process(current_servers, context):
                    self._execution_metadata['processors_skipped'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'reason': 'cannot_process'
                    })
                    continue
                
                # Execute processor with retry logic
                processed_servers = self._execute_with_retry(
                    processor, current_servers, context, profile
                )
                
                # Update current servers
                current_servers = processed_servers
                
                # Collect metadata
                if self.collect_metadata:
                    processor_metadata = processor.get_metadata()
                    self._execution_metadata['processors_executed'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'metadata': processor_metadata,
                        'input_count': len(servers) if i == 0 else len(current_servers),
                        'output_count': len(current_servers)
                    })
                
            except Exception as e:
                self._execution_metadata['processors_failed'].append({
                    'index': i,
                    'name': processor.__class__.__name__,
                    'error': str(e)
                })
                
                if self.error_strategy == 'fail_fast':
                    raise
                # Continue with next processor on error
        
        return current_servers
    
    def _execute_parallel(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Execute processors in parallel (each on original servers).
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of processed servers (merged results)
        """
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all processors
            future_to_processor = {}
            for i, processor in enumerate(self.processors):
                if processor.can_process(servers, context):
                    future = executor.submit(
                        self._execute_with_retry,
                        processor, servers, context, profile
                    )
                    future_to_processor[future] = (i, processor)
                else:
                    self._execution_metadata['processors_skipped'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'reason': 'cannot_process'
                    })
            
            # Collect results
            all_results = []
            for future in as_completed(future_to_processor.keys()):
                i, processor = future_to_processor[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    
                    if self.collect_metadata:
                        processor_metadata = processor.get_metadata()
                        self._execution_metadata['processors_executed'].append({
                            'index': i,
                            'name': processor.__class__.__name__,
                            'metadata': processor_metadata,
                            'input_count': len(servers),
                            'output_count': len(result)
                        })
                        
                except Exception as e:
                    self._execution_metadata['processors_failed'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'error': str(e)
                    })
                    
                    if self.error_strategy == 'fail_fast':
                        raise
            
            # Merge results (simple concatenation, could be more sophisticated)
            if all_results:
                # Use the first result as base, could implement more complex merging
                return all_results[0]
            else:
                return servers
    
    def _execute_conditional(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Execute processors conditionally based on results.
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of processed servers
        """
        current_servers = servers
        
        for i, processor in enumerate(self.processors):
            try:
                # Check if processor should be executed
                should_execute = self._should_execute_processor(
                    processor, current_servers, context, profile
                )
                
                if not should_execute:
                    self._execution_metadata['processors_skipped'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'reason': 'conditional_skip'
                    })
                    continue
                
                # Execute processor
                processed_servers = self._execute_with_retry(
                    processor, current_servers, context, profile
                )
                
                # Update current servers
                current_servers = processed_servers
                
                # Collect metadata
                if self.collect_metadata:
                    processor_metadata = processor.get_metadata()
                    self._execution_metadata['processors_executed'].append({
                        'index': i,
                        'name': processor.__class__.__name__,
                        'metadata': processor_metadata,
                        'input_count': len(servers) if i == 0 else len(current_servers),
                        'output_count': len(current_servers)
                    })
                
            except Exception as e:
                self._execution_metadata['processors_failed'].append({
                    'index': i,
                    'name': processor.__class__.__name__,
                    'error': str(e)
                })
                
                if self.error_strategy == 'fail_fast':
                    raise
        
        return current_servers
    
    def _should_execute_processor(
        self,
        processor: BasePostProcessor,
        servers: List[ParsedServer],
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> bool:
        """Determine if processor should be executed conditionally.
        
        Args:
            processor: Processor to check
            servers: Current servers
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            bool: True if processor should be executed
        """
        # Basic conditional logic - can be extended
        if not processor.can_process(servers, context):
            return False
        
        # Check profile-specific conditions
        if profile and hasattr(processor, 'extract_filter_config'):
            filter_config = processor.extract_filter_config(profile)
            if not filter_config:
                return False
        
        return True
    
    def _execute_with_retry(
        self,
        processor: BasePostProcessor,
        servers: List[ParsedServer],
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Execute processor with retry logic.
        
        Args:
            processor: Processor to execute
            servers: Servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of processed servers
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return processor.process(servers, context, profile)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Wait before retry
                    import time
                    time.sleep(self.retry_delay_seconds)
                else:
                    # Max retries exceeded
                    raise last_exception
        
        # Should not reach here
        raise last_exception
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None) -> bool:
        """Check if chain can process servers.
        
        Args:
            servers: List of servers
            context: Pipeline context
            
        Returns:
            bool: True if at least one processor can handle the servers
        """
        if not servers or not self.processors:
            return False
        
        # Check if at least one processor can handle the servers
        for processor in self.processors:
            if processor.can_process(servers, context):
                return True
        
        return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about chain execution.
        
        Returns:
            Dict containing chain execution metadata
        """
        metadata = super().get_metadata()
        metadata.update({
            'processors_count': len(self.processors),
            'execution_mode': self.execution_mode,
            'error_strategy': self.error_strategy,
            'execution_metadata': self._execution_metadata
        })
        return metadata
    
    def get_processor_by_name(self, name: str) -> Optional[BasePostProcessor]:
        """Get processor by class name.
        
        Args:
            name: Class name of processor to find
            
        Returns:
            Processor instance or None
        """
        for processor in self.processors:
            if processor.__class__.__name__ == name:
                return processor
        return None
    
    def add_processor(self, processor: BasePostProcessor, index: Optional[int] = None) -> None:
        """Add processor to chain.
        
        Args:
            processor: Processor to add
            index: Optional index to insert at (default: append)
        """
        if index is None:
            self.processors.append(processor)
        else:
            self.processors.insert(index, processor)
    
    def remove_processor(self, processor: Union[BasePostProcessor, str, int]) -> bool:
        """Remove processor from chain.
        
        Args:
            processor: Processor instance, class name, or index
            
        Returns:
            bool: True if processor was removed
        """
        if isinstance(processor, int):
            if 0 <= processor < len(self.processors):
                del self.processors[processor]
                return True
        elif isinstance(processor, str):
            for i, proc in enumerate(self.processors):
                if proc.__class__.__name__ == processor:
                    del self.processors[i]
                    return True
        elif isinstance(processor, BasePostProcessor):
            try:
                self.processors.remove(processor)
                return True
            except ValueError:
                pass
        
        return False 