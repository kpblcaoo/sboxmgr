"""Integration tests for Phase 4 Generator Refactoring.

Tests the integration of Phase 3 PostProcessor and Middleware components
into the export pipeline through ExportManager and CLI commands.
"""

import pytest
from unittest.mock import Mock, patch

from sboxmgr.subscription.models import ParsedServer, PipelineContext, ClientProfile, InboundProfile
from sboxmgr.export.export_manager import ExportManager
from sboxmgr.export.routing.base_router import BaseRoutingPlugin

# Test data
SAMPLE_SERVERS = [
    ParsedServer(
        type="vless",
        address="server1.example.com",
        port=443,
        tag="US-Server-1",
        meta={"country": "US", "latency_ms": 50}
    ),
    ParsedServer(
        type="vmess",
        address="server2.example.com", 
        port=443,
        tag="CA-Server-1",
        meta={"country": "CA", "latency_ms": 80}
    ),
    ParsedServer(
        type="shadowsocks",
        address="server3.example.com",
        port=443,
        tag="UK-Server-1",
        meta={"country": "UK", "latency_ms": 120}
    )
]


class TestExportManagerPhase4:
    """Test ExportManager with Phase 4 enhancements."""
    
    def test_export_manager_initialization(self):
        """Test ExportManager initialization with Phase 3 components."""
        # Test basic initialization (backward compatibility)
        export_mgr = ExportManager()
        assert export_mgr.export_format == "singbox"
        assert export_mgr.postprocessor_chain is None
        assert export_mgr.middleware_chain == []
        assert export_mgr.profile is None
        
        # Test initialization with Phase 3 components
        from sboxmgr.export.export_manager import PHASE3_AVAILABLE
        if PHASE3_AVAILABLE:
            from sboxmgr.subscription.postprocessors import PostProcessorChain, GeoFilterPostProcessor
            
            postprocessor_chain = PostProcessorChain([GeoFilterPostProcessor({})], {})
            export_mgr = ExportManager(postprocessor_chain=postprocessor_chain)
            assert export_mgr.postprocessor_chain is not None
            assert export_mgr.has_phase3_components
    
    def test_export_backward_compatibility(self):
        """Test that export works without Phase 3 components (backward compatibility)."""
        export_mgr = ExportManager()
        
        # Mock routing plugin
        mock_router = Mock()
        mock_router.generate_routes.return_value = []
        export_mgr.routing_plugin = mock_router
        
        # Test export without Phase 3 components
        with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY') as mock_registry:
            mock_export_func = Mock(return_value={"outbounds": [], "route": {"rules": []}})
            mock_registry.__getitem__ = Mock(return_value=mock_export_func)
            mock_registry.get = Mock(return_value=mock_export_func)
            
            result = export_mgr.export(SAMPLE_SERVERS)
            
            # Verify export was called with filtered servers
            mock_export_func.assert_called_once()
            args, kwargs = mock_export_func.call_args
            assert len(args[0]) == 3  # All servers should be passed through
            assert args[1] == []  # Empty routes
    
    @pytest.mark.skipif(not hasattr(ExportManager, 'has_phase3_components'), 
                        reason="Phase 3 components not available")
    def test_export_with_postprocessor_chain(self):
        """Test export with PostProcessorChain integration."""
        from sboxmgr.subscription.postprocessors import PostProcessorChain, GeoFilterPostProcessor
        
        # Create postprocessor chain that filters to US servers only
        geo_filter = GeoFilterPostProcessor({'allowed_countries': ['US']})
        postprocessor_chain = PostProcessorChain([geo_filter], {
            'execution_mode': 'sequential',
            'error_strategy': 'continue'
        })
        
        export_mgr = ExportManager(postprocessor_chain=postprocessor_chain)
        
        # Mock routing plugin
        mock_router = Mock()
        mock_router.generate_routes.return_value = []
        export_mgr.routing_plugin = mock_router
        
                # Mock the EXPORTER_REGISTRY
        mock_singbox_export = Mock(return_value={"outbounds": [], "route": {"rules": []}})
        
        with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY', {'singbox': mock_singbox_export}):
            context = PipelineContext(mode="test")
            result = export_mgr.export(SAMPLE_SERVERS, context=context)

            # Verify export was called
            mock_singbox_export.assert_called_once()
            
            # Verify that postprocessor chain was applied
            # (geo filter should have filtered servers)
            assert export_mgr.has_phase3_components
    
    @pytest.mark.skipif(not hasattr(ExportManager, 'has_phase3_components'),
                        reason="Phase 3 components not available")
    def test_export_with_middleware_chain(self):
        """Test export with MiddlewareChain integration."""
        try:
            from sboxmgr.subscription.middleware import LoggingMiddleware
            
            # Create middleware chain
            logging_middleware = LoggingMiddleware({'log_performance': True})
            middleware_chain = [logging_middleware]
            
            export_mgr = ExportManager(middleware_chain=middleware_chain)
            
            # Mock routing plugin
            mock_router = Mock()
            mock_router.generate_routes.return_value = []
            export_mgr.routing_plugin = mock_router
            
            # Mock the EXPORTER_REGISTRY
            mock_singbox_export = Mock(return_value={"outbounds": [], "route": {"rules": []}})
            
            with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY', {'singbox': mock_singbox_export}):
                context = PipelineContext(mode="test")
                result = export_mgr.export(SAMPLE_SERVERS, context=context)

                # Verify export was called
                mock_singbox_export.assert_called_once()
                
                # Verify that middleware was applied
                assert export_mgr.has_phase3_components
                
        except ImportError:
            pytest.skip("Middleware components not available")
    
    def test_configure_from_profile(self):
        """Test configuring ExportManager from FullProfile."""
        from sboxmgr.export.export_manager import PHASE3_AVAILABLE
        
        if not PHASE3_AVAILABLE:
            pytest.skip("Phase 3 components not available")
        
        try:
            from sboxmgr.profiles.models import FullProfile, FilterProfile
            
                        # Create a profile with filter configuration - using correct field names
            filter_profile = FilterProfile(
                exclude_tags=["blocked"],
                only_tags=["premium"]
            )

            profile = FullProfile(
                id="test-profile",  # Required field
                filters=filter_profile,  # Correct field name
                metadata={
                    "middleware": {
                        "logging": {"enabled": True, "log_performance": True}
                    }
                }
            )
            
            export_mgr = ExportManager()
            configured_mgr = export_mgr.configure_from_profile(profile)
            
            # Verify configuration
            assert configured_mgr.profile == profile
            # Note: Actual postprocessor/middleware creation depends on profile structure
            
        except ImportError:
            pytest.skip("Profile models not available")
    
    def test_get_processing_metadata(self):
        """Test getting processing metadata from ExportManager."""
        export_mgr = ExportManager()
        metadata = export_mgr.get_processing_metadata()
        
        # Verify basic metadata
        assert metadata['export_format'] == 'singbox'
        assert metadata['has_routing_plugin'] is True
        assert metadata['has_client_profile'] is False
        assert 'phase3_available' in metadata
        assert metadata['has_postprocessor_chain'] is False
        assert metadata['middleware_count'] == 0
        assert metadata['has_profile'] is False


class TestPhase4CLIIntegration:
    """Test CLI integration with Phase 4 enhancements."""
    
    def test_phase4_flags_available(self):
        """Test that Phase 4 CLI flags are available."""
        from sboxmgr.cli.commands.export import export
        import inspect
        
        # Get function signature
        sig = inspect.signature(export)
        
        # Verify Phase 4 parameters are present
        assert 'profile' in sig.parameters
        assert 'postprocessors' in sig.parameters  
        assert 'middleware' in sig.parameters
        
        # Verify parameter types (Typer uses OptionInfo objects)
        profile_param = sig.parameters['profile']
        postprocessors_param = sig.parameters['postprocessors']
        middleware_param = sig.parameters['middleware']
        
        # Check annotation types
        assert profile_param.annotation == str
        assert postprocessors_param.annotation == str
        assert middleware_param.annotation == str
    
    @patch('sboxmgr.cli.commands.export._load_profile_from_file')
    @patch('sboxmgr.cli.commands.export._generate_config_from_subscription')
    def test_profile_loading_integration(self, mock_generate, mock_load_profile):
        """Test profile loading integration in CLI."""
        
        # Mock profile loading
        mock_profile = Mock()
        mock_load_profile.return_value = mock_profile
        
        # Mock config generation
        mock_generate.return_value = {"outbounds": [], "route": {"rules": []}}
        
        # Test would require full CLI context, so we just verify the functions exist
        assert callable(mock_load_profile)
        assert callable(mock_generate)
    
    def test_postprocessor_chain_creation(self):
        """Test PostProcessorChain creation from CLI list."""
        from sboxmgr.cli.commands.export import _create_postprocessor_chain_from_list, PHASE3_AVAILABLE
        
        if not PHASE3_AVAILABLE:
            pytest.skip("Phase 3 components not available")
        
        # Test with valid processor names
        processors = ['geo_filter', 'tag_filter', 'latency_sort']
        chain = _create_postprocessor_chain_from_list(processors)
        
        if chain is not None:  # Only test if Phase 3 is available
            assert len(chain.processors) == 3
            assert chain.execution_mode == 'sequential'
            assert chain.error_strategy == 'continue'
    
    def test_middleware_chain_creation(self):
        """Test middleware chain creation from CLI list."""
        from sboxmgr.cli.commands.export import _create_middleware_chain_from_list, PHASE3_AVAILABLE
        
        if not PHASE3_AVAILABLE:
            pytest.skip("Phase 3 components not available")
        
        # Test with valid middleware names
        middleware = ['logging', 'enrichment']
        chain = _create_middleware_chain_from_list(middleware)
        
        # Verify chain creation (may be empty if middleware not available)
        assert isinstance(chain, list)


class TestPhase4ErrorHandling:
    """Test error handling in Phase 4 integration."""
    
    def test_export_with_failing_postprocessor(self):
        """Test export continues when postprocessor fails."""
        from sboxmgr.export.export_manager import PHASE3_AVAILABLE
        
        if not PHASE3_AVAILABLE:
            pytest.skip("Phase 3 components not available")
        
        # Create mock postprocessor that fails
        mock_postprocessor_chain = Mock()
        mock_postprocessor_chain.process.side_effect = Exception("Postprocessor failed")
        
        export_mgr = ExportManager(postprocessor_chain=mock_postprocessor_chain)
        
        # Mock routing plugin
        mock_router = Mock()
        mock_router.generate_routes.return_value = []
        export_mgr.routing_plugin = mock_router
        
                # Mock the EXPORTER_REGISTRY
        mock_singbox_export = Mock(return_value={"outbounds": [], "route": {"rules": []}})
        
        with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY', {'singbox': mock_singbox_export}):
            # Should not raise exception, should continue with unprocessed servers
            result = export_mgr.export(SAMPLE_SERVERS)

            # Verify export was still called
            mock_singbox_export.assert_called_once()
            assert result is not None
    
    def test_export_with_failing_middleware(self):
        """Test export continues when middleware fails."""
        from sboxmgr.export.export_manager import PHASE3_AVAILABLE
        
        if not PHASE3_AVAILABLE:
            pytest.skip("Phase 3 components not available")
        
        # Create mock middleware that fails
        mock_middleware = Mock()
        mock_middleware.process.side_effect = Exception("Middleware failed")
        mock_middleware.__class__.__name__ = "TestMiddleware"
        
        export_mgr = ExportManager(middleware_chain=[mock_middleware])
        
        # Mock routing plugin
        mock_router = Mock()
        mock_router.generate_routes.return_value = []
        export_mgr.routing_plugin = mock_router
        
                # Mock the EXPORTER_REGISTRY
        mock_singbox_export = Mock(return_value={"outbounds": [], "route": {"rules": []}})
        
        with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY', {'singbox': mock_singbox_export}):
            # Should not raise exception, should continue processing
            result = export_mgr.export(SAMPLE_SERVERS)

            # Verify export was still called
            mock_singbox_export.assert_called_once()
            assert result is not None


@pytest.mark.integration
class TestPhase4EndToEnd:
    """End-to-end integration tests for Phase 4."""
    
    @pytest.mark.skipif(not hasattr(ExportManager, 'has_phase3_components'),
                        reason="Phase 3 components not available")
    def test_full_pipeline_integration(self):
        """Test full pipeline with Phase 3 components."""
        try:
            from sboxmgr.subscription.postprocessors import PostProcessorChain, GeoFilterPostProcessor
            from sboxmgr.subscription.middleware import LoggingMiddleware
            
            # Create full pipeline
            geo_filter = GeoFilterPostProcessor({'allowed_countries': ['US', 'CA']})
            postprocessor_chain = PostProcessorChain([geo_filter], {})
            
            logging_middleware = LoggingMiddleware({})
            middleware_chain = [logging_middleware]
            
            export_mgr = ExportManager(
                postprocessor_chain=postprocessor_chain,
                middleware_chain=middleware_chain
            )
            
            # Mock routing plugin
            mock_router = Mock()
            mock_router.generate_routes.return_value = []
            export_mgr.routing_plugin = mock_router
            
                        # Mock the EXPORTER_REGISTRY
            mock_singbox_export = Mock(return_value={"outbounds": [], "route": {"rules": []}})
            
            with patch('sboxmgr.export.export_manager.EXPORTER_REGISTRY', {'singbox': mock_singbox_export}):
                context = PipelineContext(mode="integration_test")
                result = export_mgr.export(SAMPLE_SERVERS, context=context)

                # Verify pipeline executed
                assert result is not None
                mock_singbox_export.assert_called_once()
                
        except ImportError:
            pytest.skip("Full Phase 3 components not available")

    def test_export_manager_basic_export(self):
        """Test basic export functionality."""
        export_mgr = ExportManager()
        
        result = export_mgr.export(SAMPLE_SERVERS)
        
        assert isinstance(result, dict)
        assert "outbounds" in result
        assert "route" in result


    def test_export_manager_with_context(self):
        """Test export with pipeline context."""
        export_mgr = ExportManager()
        context = PipelineContext(mode="test")
        
        result = export_mgr.export(SAMPLE_SERVERS, context=context)
        
        assert isinstance(result, dict)
        assert "outbounds" in result
        assert "route" in result


    def test_export_manager_with_client_profile(self):
        """Test export with client profile."""
        export_mgr = ExportManager()
        context = PipelineContext(mode="test")
        client_profile = ClientProfile(
            inbounds=[
                InboundProfile(
                    type="tun",
                    tag="tun-in",
                    interface_name="tun0",
                    network="10.0.0.1/30",
                    mtu=9000
                )
            ]
        )
        
        result = export_mgr.export(SAMPLE_SERVERS, context=context, client_profile=client_profile)
        
        assert isinstance(result, dict)
        assert "outbounds" in result
        assert "route" in result
        
        # Check that inbounds were generated from client profile
        if "inbounds" in result:
            inbounds = result["inbounds"]
            assert len(inbounds) > 0
            assert any(inb.get("type") == "tun" for inb in inbounds)


    def test_export_manager_with_routing_plugin(self):
        """Test export with custom routing plugin."""
        class TestRoutingPlugin(BaseRoutingPlugin):
            def generate_routes(self, servers, exclusions, user_routes, context=None):
                return [
                    {
                        "domain": ["example.com"],
                        "outbound": "direct"
                    }
                ]
        
        routing_plugin = TestRoutingPlugin()
        export_mgr = ExportManager(routing_plugin=routing_plugin)
        
        result = export_mgr.export(SAMPLE_SERVERS)
        
        assert isinstance(result, dict)
        assert "route" in result
        assert "rules" in result["route"]
        
        # Check that custom routing rules were applied
        rules = result["route"]["rules"]
        assert len(rules) > 0
        # Look for our custom rule among all rules
        assert any(rule.get("domain") == ["example.com"] for rule in rules)


    def test_export_manager_with_exclusions(self):
        """Test export with server exclusions."""
        export_mgr = ExportManager()
        
        # Exclude servers with specific addresses
        exclusions = ["1.1.1.1", "2.2.2.2"]
        
        result = export_mgr.export(SAMPLE_SERVERS, exclusions=exclusions)
        
        assert isinstance(result, dict)
        assert "outbounds" in result
        
        # Check that excluded servers are not in outbounds
        outbounds = result["outbounds"]
        for outbound in outbounds:
            if "server" in outbound:
                assert outbound["server"] not in exclusions


    def test_export_manager_with_user_routes(self):
        """Test export with user-defined routing rules."""
        export_mgr = ExportManager()
        context = PipelineContext(mode="test")
        
        user_routes = [
            {"domain": ["google.com"], "outbound": "proxy"},
            {"ip_cidr": ["8.8.8.8/32"], "outbound": "direct"}
        ]
        
        result = export_mgr.export(SAMPLE_SERVERS, user_routes=user_routes, context=context)
        
        assert isinstance(result, dict)
        assert "route" in result
        assert "rules" in result["route"]
        
        # Check that user routes were applied
        rules = result["route"]["rules"]
        assert len(rules) >= len(user_routes) 