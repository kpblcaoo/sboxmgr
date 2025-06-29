"""Enhanced base postprocessor interface for subscription data enhancement.

This module defines the abstract base class for postprocessors that enhance
or transform parsed server data after parsing. Postprocessors can add
metadata, apply filters, perform optimizations, or implement custom
transformations before final export.

Implements Phase 3 of architectural improvements with profile integration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import ParsedServer, PipelineContext
from ...profiles.models import FullProfile, FilterProfile


class BasePostProcessor(ABC):
    """Abstract base class for subscription data postprocessors.
    
    Postprocessors transform or enhance parsed server data after the parsing
    stage. They can add geographic information, apply filtering rules,
    optimize server lists, or perform custom transformations.
    
    Phase 3 enhancements:
    - Profile-aware processing
    - Enhanced context support
    - Metadata enrichment capabilities
    - Chain-friendly interface
    """
    
    plugin_type = "postprocessor"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize postprocessor with optional configuration.
        
        Args:
            config: Optional configuration dictionary for the postprocessor
        """
        self.config = config or {}
    
    @abstractmethod
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Process and transform parsed server data.
        
        Args:
            servers: List of ParsedServer objects to process
            context: Pipeline context containing processing configuration
            profile: Full profile configuration for profile-aware processing
            
        Returns:
            List[ParsedServer]: Processed servers after transformation
            
        Raises:
            NotImplementedError: If called directly on base class
        """
        pass
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None) -> bool:
        """Check if this postprocessor can process the given servers.
        
        Args:
            servers: List of servers to check
            context: Pipeline context
            
        Returns:
            bool: True if this postprocessor can handle the servers
        """
        return len(servers) > 0
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this postprocessor.
        
        Returns:
            Dict containing postprocessor metadata
        """
        return {
            "name": self.__class__.__name__,
            "type": self.plugin_type,
            "config": self.config
        }


class ProfileAwarePostProcessor(BasePostProcessor):
    """Base class for postprocessors that use profile configuration.
    
    This class provides helper methods for extracting configuration
    from profiles and applying profile-based transformations.
    """
    
    def extract_filter_config(self, profile: Optional[FullProfile]) -> Optional[FilterProfile]:
        """Extract filter configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            FilterProfile or None if no profile provided
        """
        return profile.filters if profile else None
    
    def should_exclude_server(self, server: ParsedServer, filter_config: Optional[FilterProfile]) -> bool:
        """Check if server should be excluded based on filter configuration.
        
        Args:
            server: Server to check
            filter_config: Filter configuration
            
        Returns:
            bool: True if server should be excluded
        """
        if not filter_config:
            return False
        
        # Check tag-based exclusions
        server_tag = server.tag or server.meta.get('tag', '')
        
        # Exclude if server tag is in exclude_tags
        if server_tag and server_tag in filter_config.exclude_tags:
            return True
        
        # Exclude if only_tags is specified and server tag is not in it
        if filter_config.only_tags and server_tag not in filter_config.only_tags:
            return True
        
        # Check server name/address exclusions
        server_name = f"{server.address}:{server.port}"
        if server_name in filter_config.exclusions:
            return True
        
        return False


class ChainablePostProcessor(ProfileAwarePostProcessor):
    """Base class for postprocessors designed to work in chains.
    
    Provides additional methods for chain coordination and
    metadata passing between processors.
    """
    
    def pre_process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
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
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
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
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
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
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
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