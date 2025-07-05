"""Core exporter functions for sing-box configuration."""

import logging
from typing import List, Dict, Any, Optional

from sboxmgr.subscription.models import ParsedServer, ClientProfile, PipelineContext
from .constants import SUPPORTED_PROTOCOLS, DEFAULT_URLTEST_CONFIG
from .protocol_handlers import get_protocol_dispatcher
from .config_processors import normalize_protocol_type, process_standard_server
from .inbound_generator import generate_inbounds

logger = logging.getLogger(__name__)


def process_single_server(server: ParsedServer) -> Optional[Dict[str, Any]]:
    """Process a single server and return outbound configuration.
    
    Args:
        server: ParsedServer to process.
        
    Returns:
        Outbound configuration or None if server should be skipped.
    """
    protocol_type = normalize_protocol_type(server.type)
    
    # Check protocol support
    if not is_supported_protocol(protocol_type):
        logger.warning(f"Unsupported outbound type: {server.type}, skipping {server.address}:{server.port}")
        return None
    
    # Handle special protocols
    dispatcher = get_protocol_dispatcher()
    if protocol_type in dispatcher:
        return dispatcher[protocol_type](server)  # May return None
    
    # Handle standard protocols
    return process_standard_server(server, protocol_type)


def is_supported_protocol(protocol_type: str) -> bool:
    """Check if protocol is supported.
    
    Args:
        protocol_type: Protocol type to check.
        
    Returns:
        True if protocol is supported.
    """
    return protocol_type in SUPPORTED_PROTOCOLS


def create_urltest_outbound(proxy_tags: List[str]) -> Dict[str, Any]:
    """Create URLTest outbound configuration.
    
    Args:
        proxy_tags: List of proxy server tags.
        
    Returns:
        URLTest outbound configuration.
    """
    urltest_config = {
        "type": "urltest",
        "tag": "auto",
        "outbounds": proxy_tags,
    }
    urltest_config.update(DEFAULT_URLTEST_CONFIG)
    return urltest_config


def create_modern_routing_rules(proxy_tags: List[str]) -> List[Dict[str, Any]]:
    """Create modern routing rules with rule actions.
    
    Args:
        proxy_tags: List of proxy server tags.
        
    Returns:
        List of routing rules.
    """
    rules = []
    
    # Private IP ranges - direct
    rules.append({
        "ip_cidr": [
            "10.0.0.0/8",
            "172.16.0.0/12", 
            "192.168.0.0/16",
            "127.0.0.0/8"
        ],
        "outbound": "direct"
    })
    
    # Russian sites - direct
    rules.append({
        "rule_set": ["geoip-ru"],
        "outbound": "direct"
    })
    
    # Block ads and malware
    rules.append({
        "rule_set": ["geosite-ads"],
        "outbound": "block"
    })
    
    return rules


def singbox_export(
    servers: List[ParsedServer],
    routes: Optional[List[Dict[str, Any]]] = None,
    client_profile: Optional[ClientProfile] = None
) -> Dict[str, Any]:
    """Export parsed servers to sing-box configuration format (modern approach).
    
    This function exports configuration using the modern sing-box 1.11.0 approach
    with rule actions instead of legacy special outbounds.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration (optional, uses modern defaults if None).
        client_profile: Optional client profile for inbound generation.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    outbounds = []
    proxy_tags = []
    
    # Process each server
    for server in servers:
        outbound = process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])
    
    # Add URLTest outbound if there are proxy servers
    if proxy_tags:
        urltest_outbound = create_urltest_outbound(proxy_tags)
        outbounds.insert(0, urltest_outbound)
    
    # Use provided routing rules or create modern defaults
    if routes:
        routing_rules = routes
    else:
        routing_rules = create_modern_routing_rules(proxy_tags)
    
    # Determine final action
    final_action = "auto" if proxy_tags else "direct"
    
    # Build final configuration
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "final": final_action
        }
    }
    
    # Add inbounds if client profile provided
    if client_profile is not None:
        config["inbounds"] = generate_inbounds(client_profile)
    
    return config


def singbox_export_with_middleware(
    servers: List[ParsedServer],
    routes: Optional[List[Dict[str, Any]]] = None,
    client_profile: Optional[ClientProfile] = None,
    context: Optional[PipelineContext] = None
) -> Dict[str, Any]:
    """Export parsed servers to sing-box configuration format using middleware.
    
    This function exports configuration using middleware for outbound filtering
    and route configuration, providing better separation of concerns.
    
    Args:
        servers: List of ParsedServer objects to export.
        routes: Routing rules configuration (optional, uses modern defaults if None).
        client_profile: Optional client profile for inbound generation.
        context: Optional pipeline context with middleware metadata.
        
    Returns:
        Dictionary containing complete sing-box configuration with outbounds,
        routing rules, and optional inbounds section.
    """
    outbounds = []
    proxy_tags = []
    
    # Process each server
    for server in servers:
        outbound = process_single_server(server)
        if outbound:
            outbounds.append(outbound)
            proxy_tags.append(outbound["tag"])
    
    # Add URLTest outbound if there are proxy servers
    if proxy_tags:
        urltest_outbound = create_urltest_outbound(proxy_tags)
        outbounds.insert(0, urltest_outbound)
    
    # Use provided routing rules or create modern defaults
    if routes:
        routing_rules = routes
    else:
        routing_rules = create_modern_routing_rules(proxy_tags)
    
    # Determine final action from context or client_profile
    final_action = "auto"  # default
    
    # Priority: context > client_profile > default
    if context and 'routing' in context.metadata:
        context_final = context.metadata['routing'].get('final_action')
        if context_final:
            final_action = context_final
    elif client_profile and client_profile.routing:
        final_action = client_profile.routing.get("final", "auto")
    
    # Build final configuration
    config = {
        "outbounds": outbounds,
        "route": {
            "rules": routing_rules,
            "final": final_action
        }
    }
    
    # Add inbounds if client profile provided
    if client_profile:
        config["inbounds"] = generate_inbounds(client_profile)
    
    return config 