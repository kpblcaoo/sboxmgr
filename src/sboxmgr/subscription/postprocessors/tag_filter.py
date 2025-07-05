"""Tag-based filtering postprocessor implementation.

This module provides postprocessing functionality for filtering servers
based on tags and labels. It supports include/exclude tag lists, regex
patterns, and profile-based tag filtering rules.

Implements Phase 3 architecture with profile integration.
"""

import re
from typing import List, Optional, Dict, Any, Pattern
from ..registry import register
from .base import ProfileAwarePostProcessor
from ..models import ParsedServer, PipelineContext
from ...profiles.models import FullProfile


@register("tag_filter")
class TagFilterPostProcessor(ProfileAwarePostProcessor):
    """Tag-based filtering postprocessor with profile integration.
    
    Filters servers based on tag criteria defined in profiles or configuration.
    Supports exact tag matching, regex patterns, and complex tag rules.
    
    Configuration options:
    - include_tags: List of tags to include (whitelist)
    - exclude_tags: List of tags to exclude (blacklist)
    - include_patterns: List of regex patterns for tag inclusion
    - exclude_patterns: List of regex patterns for tag exclusion
    - case_sensitive: Whether tag matching is case sensitive
    - fallback_mode: What to do if server has no tags ('allow', 'block')
    - require_tags: Whether servers must have tags to be included
    
    Example:
        processor = TagFilterPostProcessor({
            'include_tags': ['premium', 'fast'],
            'exclude_tags': ['blocked', 'slow'],
            'include_patterns': [r'^US-.*', r'.*-Premium$'],
            'case_sensitive': False
        })
        filtered_servers = processor.process(servers, context, profile)

    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize tag filter with configuration.
        
        Args:
            config: Configuration dictionary with filtering options

        """
        super().__init__(config)
        self.include_tags = set(self.config.get('include_tags', []))
        self.exclude_tags = set(self.config.get('exclude_tags', []))
        self.case_sensitive = self.config.get('case_sensitive', False)
        self.fallback_mode = self.config.get('fallback_mode', 'allow')
        self.require_tags = self.config.get('require_tags', False)
        self.include_patterns = self._compile_patterns(self.config.get('include_patterns', []))
        self.exclude_patterns = self._compile_patterns(self.config.get('exclude_patterns', []))
    
    def _compile_patterns(self, patterns: List[str]) -> List[Pattern[str]]:
        """Compile regex patterns with appropriate flags.
        
        Args:
            patterns: List of regex pattern strings
            
        Returns:
            List of compiled regex patterns

        """
        compiled = []
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern, flags))
            except re.error:
                # Skip invalid patterns
                continue
        
        return compiled
    
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Filter servers based on tag criteria.
        
        Args:
            servers: List of servers to filter
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of servers that match tag criteria

        """
        if not servers:
            return servers
        
        # Extract tag configuration from profile
        tag_config = self._extract_tag_config(profile)
        
        # Apply tag filtering
        filtered_servers = []
        for server in servers:
            if self._should_include_server(server, tag_config, context):
                filtered_servers.append(server)
        
        return filtered_servers
    
    def _extract_tag_config(self, profile: Optional[FullProfile]) -> Dict[str, Any]:
        """Extract tag configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            Dictionary with tag configuration

        """
        tag_config = {
            'include_tags': self.include_tags.copy(),
            'exclude_tags': self.exclude_tags.copy(),
            'include_patterns': self.include_patterns.copy(),
            'exclude_patterns': self.exclude_patterns.copy(),
            'case_sensitive': self.case_sensitive,
            'fallback_mode': self.fallback_mode,
            'require_tags': self.require_tags
        }
        
        if not profile:
            return tag_config
        
        # Use profile filter configuration
        filter_config = self.extract_filter_config(profile)
        if filter_config:
            # Merge profile tags with configuration
            if filter_config.exclude_tags:
                tag_config['exclude_tags'].update(filter_config.exclude_tags)
            if filter_config.only_tags:
                tag_config['include_tags'].update(filter_config.only_tags)
        
        # Check for tag-specific metadata in profile
        if 'tags' in profile.metadata:
            tag_meta = profile.metadata['tags']
            if 'include' in tag_meta:
                tag_config['include_tags'].update(tag_meta['include'])
            if 'exclude' in tag_meta:
                tag_config['exclude_tags'].update(tag_meta['exclude'])
            if 'patterns' in tag_meta:
                patterns_meta = tag_meta['patterns']
                if 'include' in patterns_meta:
                    new_patterns = self._compile_patterns(patterns_meta['include'])
                    tag_config['include_patterns'].extend(new_patterns)
                if 'exclude' in patterns_meta:
                    new_patterns = self._compile_patterns(patterns_meta['exclude'])
                    tag_config['exclude_patterns'].extend(new_patterns)
        
        return tag_config
    
    def _should_include_server(
        self, 
        server: ParsedServer, 
        tag_config: Dict[str, Any],
        context: Optional[PipelineContext] = None
    ) -> bool:
        """Check if server should be included based on tag criteria.
        
        Args:
            server: Server to check
            tag_config: Tag configuration
            context: Pipeline context
            
        Returns:
            bool: True if server should be included

        """
        # Extract server tags
        server_tags = self._extract_server_tags(server)
        
        # Handle servers without tags
        if not server_tags:
            if tag_config['require_tags']:
                return False
            return tag_config['fallback_mode'] == 'allow'
        
        # Check exclude patterns first (highest priority)
        for pattern in tag_config['exclude_patterns']:
            for tag in server_tags:
                if pattern.search(tag):
                    return False
        
        # Check exclude tags
        if tag_config['exclude_tags']:
            for tag in server_tags:
                tag_to_check = tag if tag_config['case_sensitive'] else tag.lower()
                exclude_tags = tag_config['exclude_tags']
                if not tag_config['case_sensitive']:
                    exclude_tags = {t.lower() for t in exclude_tags}
                if tag_to_check in exclude_tags:
                    return False
        
        # Check include patterns
        if tag_config['include_patterns']:
            pattern_matched = False
            for pattern in tag_config['include_patterns']:
                for tag in server_tags:
                    if pattern.search(tag):
                        pattern_matched = True
                        break
                if pattern_matched:
                    break
            if not pattern_matched:
                return False
        
        # Check include tags
        if tag_config['include_tags']:
            tag_matched = False
            for tag in server_tags:
                tag_to_check = tag if tag_config['case_sensitive'] else tag.lower()
                include_tags = tag_config['include_tags']
                if not tag_config['case_sensitive']:
                    include_tags = {t.lower() for t in include_tags}
                if tag_to_check in include_tags:
                    tag_matched = True
                    break
            if not tag_matched:
                return False
        
        return True
    
    def _extract_server_tags(self, server: ParsedServer) -> List[str]:
        """Extract tags from server metadata.
        
        Args:
            server: Server to extract tags from
            
        Returns:
            List of tags for the server

        """
        tags = []
        
        # Primary tag field
        if server.tag:
            tags.append(server.tag)
        
        # Tags in metadata
        if 'tag' in server.meta and server.meta['tag']:
            tags.append(server.meta['tag'])
        
        if 'tags' in server.meta:
            meta_tags = server.meta['tags']
            if isinstance(meta_tags, list):
                tags.extend(meta_tags)
            elif isinstance(meta_tags, str):
                # Handle comma-separated tags
                tags.extend([tag.strip() for tag in meta_tags.split(',')])
        
        # Extract tags from server name/label
        if 'name' in server.meta and server.meta['name']:
            # Try to extract tags from server name (e.g., "US-Premium-01" -> ["US", "Premium", "01"])
            name_parts = re.split(r'[-_\s]+', server.meta['name'])
            tags.extend([part for part in name_parts if part])
        
        # Extract tags from the main tag field by splitting on common separators
        if server.tag:
            # Split tag on common separators and add individual parts
            tag_parts = re.split(r'[-_\s]+', server.tag)
            tags.extend([part for part in tag_parts if part and part != server.tag])
        
        # Remove duplicates and empty tags
        return list(set(tag for tag in tags if tag and tag.strip()))
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None) -> bool:
        """Check if tag filtering can be applied.
        
        Args:
            servers: List of servers
            context: Pipeline context
            
        Returns:
            bool: True if tag filtering is applicable

        """
        if not servers:
            return False
        
        # Check if any servers have tags
        for server in servers:
            if self._extract_server_tags(server):
                return True
        
        # Can still process servers without tags (fallback mode)
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this postprocessor.
        
        Returns:
            Dict containing postprocessor metadata

        """
        metadata = super().get_metadata()
        metadata.update({
            'include_tags': list(self.include_tags),
            'exclude_tags': list(self.exclude_tags),
            'include_patterns': [p.pattern for p in self.include_patterns],
            'exclude_patterns': [p.pattern for p in self.exclude_patterns],
            'case_sensitive': self.case_sensitive,
            'fallback_mode': self.fallback_mode,
            'require_tags': self.require_tags
        })
        return metadata 