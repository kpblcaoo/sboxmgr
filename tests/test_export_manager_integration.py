"""Tests for ExportManager integration with middleware."""

from src.sboxmgr.export.export_manager import ExportManager
from src.sboxmgr.export.routing.default_router import DefaultRouter
from src.sboxmgr.subscription.models import ClientProfile, ParsedServer, PipelineContext


class TestExportManagerMiddlewareIntegration:
    """Test ExportManager integration with middleware."""

    def test_auto_configure_middleware_from_client_profile(self):
        """Test automatic middleware configuration from client profile."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
            ParsedServer(
                type="shadowsocks",
                address="9.10.11.12",
                port=8388,
                password="test-pass",
                tag="ss-server",
            ),
        ]

        # Create client profile with both exclude_outbounds and routing
        client_profile = ClientProfile(
            routing={"final": "block"}, exclude_outbounds=["vmess", "shadowsocks"]
        )

        # Create export manager with client profile
        export_mgr = ExportManager(
            routing_plugin=DefaultRouter(), client_profile=client_profile
        )

        # Check that middleware was auto-configured
        assert len(export_mgr.middleware_chain) >= 1

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that final action is set correctly
        route = config["route"]
        assert route["final"] == "block"

        # Check that excluded outbounds are not in the result
        outbounds = config["outbounds"]
        outbound_types = [
            o.get("type") for o in outbounds if o.get("type") != "urltest"
        ]
        assert "vless" in outbound_types
        assert "vmess" not in outbound_types
        assert "shadowsocks" not in outbound_types

    def test_export_manager_with_only_exclude_outbounds(self):
        """Test ExportManager with only exclude_outbounds configuration."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create client profile with only exclude_outbounds
        client_profile = ClientProfile(exclude_outbounds=["vmess"])

        # Create export manager
        export_mgr = ExportManager(
            routing_plugin=DefaultRouter(), client_profile=client_profile
        )

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that vmess is excluded but vless remains
        outbounds = config["outbounds"]
        outbound_types = [
            o.get("type") for o in outbounds if o.get("type") != "urltest"
        ]
        assert "vless" in outbound_types
        assert "vmess" not in outbound_types

        # Check that final action uses default
        route = config["route"]
        assert route["final"] == "auto"  # Default from modern routing rules

    def test_export_manager_with_only_routing(self):
        """Test ExportManager with only routing configuration."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create client profile with only routing
        client_profile = ClientProfile(routing={"final": "direct"})

        # Create export manager
        export_mgr = ExportManager(
            routing_plugin=DefaultRouter(), client_profile=client_profile
        )

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that final action is set correctly
        route = config["route"]
        assert route["final"] == "direct"

        # Check that all servers are included (no filtering)
        outbounds = config["outbounds"]
        outbound_types = [
            o.get("type") for o in outbounds if o.get("type") != "urltest"
        ]
        assert "vless" in outbound_types
        assert "vmess" in outbound_types

    def test_export_manager_middleware_metadata(self):
        """Test that middleware metadata is preserved in context."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create client profile
        client_profile = ClientProfile(
            routing={"final": "block"}, exclude_outbounds=["vmess"]
        )

        # Create export manager
        export_mgr = ExportManager(
            routing_plugin=DefaultRouter(), client_profile=client_profile
        )

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that middleware metadata is preserved
        assert "outbound_filter" in context.metadata
        assert "routing" in context.metadata

        outbound_meta = context.metadata["outbound_filter"]
        routing_meta = context.metadata["routing"]

        assert outbound_meta["excluded_count"] == 1
        assert routing_meta["final_action"] == "block"

    def test_export_manager_without_client_profile(self):
        """Test ExportManager without client profile (no auto-configuration)."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create export manager without client profile
        export_mgr = ExportManager(routing_plugin=DefaultRouter())

        # Check that no middleware is auto-configured
        assert len(export_mgr.middleware_chain) == 0

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that all servers are included and default final action is used
        outbounds = config["outbounds"]
        outbound_types = [
            o.get("type") for o in outbounds if o.get("type") != "urltest"
        ]
        assert "vless" in outbound_types
        assert "vmess" in outbound_types

        route = config["route"]
        assert route["final"] == "auto"  # Default

    def test_export_manager_manual_middleware_override(self):
        """Test that manual middleware configuration overrides auto-configuration."""
        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create client profile
        client_profile = ClientProfile(
            routing={"final": "block"}, exclude_outbounds=["vmess"]
        )

        # Create manual middleware configuration
        from src.sboxmgr.subscription.middleware import OutboundFilterMiddleware

        manual_middleware = [
            OutboundFilterMiddleware(
                {
                    "exclude_types": ["vless"],  # Different from client_profile
                    "strict_mode": False,
                }
            )
        ]

        # Create export manager with manual middleware
        export_mgr = ExportManager(
            routing_plugin=DefaultRouter(),
            client_profile=client_profile,
            middleware_chain=manual_middleware,
        )

        # Export configuration
        context = PipelineContext(mode="test")
        config = export_mgr.export(servers, context=context)

        # Check that manual middleware takes precedence
        outbounds = config["outbounds"]
        outbound_types = [
            o.get("type") for o in outbounds if o.get("type") != "urltest"
        ]
        assert "vless" not in outbound_types  # Manual middleware excluded vless
        assert "vmess" in outbound_types  # Client_profile exclude was overridden
