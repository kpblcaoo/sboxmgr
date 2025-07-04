"""Tests for middleware integration with export functionality."""

import pytest
from src.sboxmgr.subscription.models import ParsedServer, ClientProfile, PipelineContext
from src.sboxmgr.subscription.exporters.singbox_exporter import singbox_export_with_middleware
from src.sboxmgr.subscription.middleware import OutboundFilterMiddleware, RouteConfigMiddleware
from src.sboxmgr.profiles.models import FullProfile


class TestMiddlewareIntegration:
    """Test middleware integration with export functionality."""
    
    def test_outbound_filter_middleware_basic(self):
        """Test basic outbound filtering middleware functionality."""
        # Create test servers
        servers = [
            ParsedServer(type="vless", address="1.2.3.4", port=443, uuid="test-uuid", tag="vless-server"),
            ParsedServer(type="vmess", address="5.6.7.8", port=1080, uuid="test-vmess-uuid", tag="vmess-server"),
            ParsedServer(type="shadowsocks", address="9.10.11.12", port=8388, password="test-pass", tag="ss-server"),
        ]
        
        # Create middleware
        middleware = OutboundFilterMiddleware({
            'exclude_types': ['vmess', 'shadowsocks']
        })
        
        # Process servers
        context = PipelineContext(mode="test")
        filtered_servers = middleware.process(servers, context)
        
        # Check filtering results
        assert len(filtered_servers) == 1
        assert filtered_servers[0].type == "vless"
        
        # Check metadata
        assert 'outbound_filter' in context.metadata
        metadata = context.metadata['outbound_filter']
        # Check that excluded_types contains the right items (order doesn't matter)
        assert set(metadata['excluded_types']) == {'vmess', 'shadowsocks'}
        assert metadata['excluded_count'] == 2
        assert metadata['original_count'] == 3
        assert metadata['filtered_count'] == 1
    
    def test_route_config_middleware_basic(self):
        """Test basic route configuration middleware functionality."""
        # Create test servers
        servers = [
            ParsedServer(type="vless", address="1.2.3.4", port=443, uuid="test-uuid", tag="vless-server"),
        ]
        
        # Create middleware
        middleware = RouteConfigMiddleware({
            'final_action': 'direct',
            'override_mode': 'profile_overrides'
        })
        
        # Process servers
        context = PipelineContext(mode="test")
        processed_servers = middleware.process(servers, context)
        
        # Check that servers are unchanged
        assert len(processed_servers) == 1
        assert processed_servers[0].type == "vless"
        
        # Check routing metadata
        assert 'routing' in context.metadata
        routing_meta = context.metadata['routing']
        assert routing_meta['final_action'] == 'direct'
        assert routing_meta['configured_by'] == 'route_config_middleware'
        assert routing_meta['override_mode'] == 'profile_overrides'
    
    def test_middleware_with_profile_integration(self):
        """Test middleware integration with profile configuration."""
        # Create test servers
        servers = [
            ParsedServer(type="vless", address="1.2.3.4", port=443, uuid="test-uuid", tag="vless-server"),
            ParsedServer(type="vmess", address="5.6.7.8", port=1080, uuid="test-vmess-uuid", tag="vmess-server"),
        ]
        
        # Create client profile
        client_profile = ClientProfile(
            routing={"final": "block"},
            exclude_outbounds=["vmess"]
        )
        
        # Create full profile with client profile in metadata
        profile = FullProfile(
            id="test-profile",
            metadata={
                "client_profile": client_profile.model_dump()
            }
        )
        
        # Create middleware
        outbound_filter = OutboundFilterMiddleware()
        route_config = RouteConfigMiddleware()
        
        # Process with middleware
        context = PipelineContext(mode="test")
        
        # Apply outbound filter
        filtered_servers = outbound_filter.process(servers, context, profile)
        assert len(filtered_servers) == 1
        assert filtered_servers[0].type == "vless"
        
        # Apply route config
        processed_servers = route_config.process(filtered_servers, context, profile)
        
        # Check routing metadata
        assert 'routing' in context.metadata
        routing_meta = context.metadata['routing']
        assert routing_meta['final_action'] == 'block'
        assert routing_meta['config_source'] == 'client_profile'
    
    def test_export_with_middleware_integration(self):
        """Test export function with middleware integration."""
        # Create test servers
        servers = [
            ParsedServer(type="vless", address="1.2.3.4", port=443, uuid="test-uuid", tag="vless-server"),
            ParsedServer(type="vmess", address="5.6.7.8", port=1080, uuid="test-vmess-uuid", tag="vmess-server"),
        ]
        
        # Create client profile
        client_profile = ClientProfile(
            routing={"final": "direct"},
            exclude_outbounds=["vmess"]
        )
        
        # Create context with routing metadata (as if set by middleware)
        context = PipelineContext(mode="test")
        context.metadata['routing'] = {
            'final_action': 'block',  # Override from middleware
            'configured_by': 'route_config_middleware'
        }
        
        # Apply outbound filter middleware first
        outbound_filter = OutboundFilterMiddleware()
        filtered_servers = outbound_filter.process(servers, context)
        
        # Export using middleware-aware function with filtered servers
        config = singbox_export_with_middleware(
            filtered_servers, 
            client_profile=client_profile,
            context=context
        )
        
        # Check that final action comes from context (middleware)
        route = config["route"]
        assert route["final"] == "block"
        
        # Check that vmess server is excluded (handled by middleware)
        outbounds = config["outbounds"]
        outbound_types = [o.get("type") for o in outbounds if o.get("type") != "urltest"]
        assert "vless" in outbound_types
        assert "vmess" not in outbound_types
    
    def test_middleware_chain_processing(self):
        """Test processing servers through a chain of middleware."""
        # Create test servers
        servers = [
            ParsedServer(type="vless", address="1.2.3.4", port=443, uuid="test-uuid", tag="vless-server"),
            ParsedServer(type="vmess", address="5.6.7.8", port=1080, uuid="test-vmess-uuid", tag="vmess-server"),
            ParsedServer(type="shadowsocks", address="9.10.11.12", port=8388, password="test-pass", tag="ss-server"),
        ]
        
        # Create middleware chain
        outbound_filter = OutboundFilterMiddleware({
            'exclude_types': ['vmess']
        })
        route_config = RouteConfigMiddleware({
            'final_action': 'proxy-out'
        })
        
        # Process through chain
        context = PipelineContext(mode="test")
        
        # Step 1: Outbound filtering
        filtered_servers = outbound_filter.process(servers, context)
        assert len(filtered_servers) == 2
        assert all(s.type in ["vless", "shadowsocks"] for s in filtered_servers)
        
        # Step 2: Route configuration
        processed_servers = route_config.process(filtered_servers, context)
        assert len(processed_servers) == 2
        
        # Check metadata from both middleware
        assert 'outbound_filter' in context.metadata
        assert 'routing' in context.metadata
        
        outbound_meta = context.metadata['outbound_filter']
        routing_meta = context.metadata['routing']
        
        assert outbound_meta['excluded_count'] == 1
        assert routing_meta['final_action'] == 'proxy-out'
    
    def test_middleware_strict_mode(self):
        """Test middleware strict mode behavior."""
        # Create test servers (all vmess)
        servers = [
            ParsedServer(type="vmess", address="1.2.3.4", port=1080, uuid="test-uuid", tag="vmess-1"),
            ParsedServer(type="vmess", address="5.6.7.8", port=1080, uuid="test-vmess-uuid", tag="vmess-2"),
        ]
        
        # Create middleware with strict mode
        middleware = OutboundFilterMiddleware({
            'exclude_types': ['vmess'],
            'strict_mode': True
        })
        
        # Process servers - should raise exception
        context = PipelineContext(mode="test")
        with pytest.raises(ValueError, match="All servers were excluded"):
            middleware.process(servers, context)
    
    def test_middleware_override_modes(self):
        """Test different override modes in route config middleware."""
        # Create client profile
        client_profile = ClientProfile(
            routing={"final": "block"}
        )
        
        # Create full profile
        profile = FullProfile(
            id="test-profile",
            metadata={
                "client_profile": client_profile.model_dump()
            }
        )
        
        # Test profile_overrides mode
        middleware_profile = RouteConfigMiddleware({
            'final_action': 'direct',
            'override_mode': 'profile_overrides'
        })
        
        context = PipelineContext(mode="test")
        middleware_profile.process([], context, profile)
        
        routing_meta = context.metadata['routing']
        assert routing_meta['final_action'] == 'block'  # Profile overrides config
        
        # Test config_overrides mode
        middleware_config = RouteConfigMiddleware({
            'final_action': 'direct',
            'override_mode': 'config_overrides'
        })
        
        context = PipelineContext(mode="test")
        middleware_config.process([], context, profile)
        
        routing_meta = context.metadata['routing']
        assert routing_meta['final_action'] == 'direct'  # Config overrides profile 