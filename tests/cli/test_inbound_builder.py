"""Tests for InboundBuilder class.

Tests the inbound configuration builder functionality including
parameter validation, security defaults, and error handling.
"""

import pytest
from sboxmgr.cli.inbound_builder import InboundBuilder, build_client_profile_from_cli
from sboxmgr.subscription.models import ClientProfile, InboundProfile


class TestInboundBuilder:
    """Test cases for InboundBuilder class."""
    
    def test_empty_builder_fails(self):
        """Test that empty builder raises error on build."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="At least one inbound must be configured"):
            builder.build()
    
    def test_add_tun_defaults(self):
        """Test TUN inbound with default parameters."""
        builder = InboundBuilder()
        profile = builder.add_tun().build()
        
        assert len(profile.inbounds) == 1
        inbound = profile.inbounds[0]
        assert inbound.type == "tun"
        assert inbound.options["address"] == ["198.18.0.1/16"]
        assert inbound.options["mtu"] == 1500
        assert inbound.options["stack"] == "mixed"
        assert inbound.options["auto_route"] is True
        assert inbound.options["tag"] == "tun-in"
    
    def test_add_tun_custom_params(self):
        """Test TUN inbound with custom parameters."""
        builder = InboundBuilder()
        profile = builder.add_tun(
            address="10.0.0.1/24",
            mtu=1400,
            stack="system",
            auto_route=False
        ).build()
        
        inbound = profile.inbounds[0]
        assert inbound.options["address"] == ["10.0.0.1/24"]
        assert inbound.options["mtu"] == 1400
        assert inbound.options["stack"] == "system"
        assert inbound.options["auto_route"] is False
    
    def test_add_tun_invalid_mtu(self):
        """Test TUN inbound with invalid MTU."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="MTU must be between 576 and 9000"):
            builder.add_tun(mtu=100)
    
    def test_add_tun_invalid_stack(self):
        """Test TUN inbound with invalid stack."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="Invalid stack"):
            builder.add_tun(stack="invalid")
    
    def test_add_socks_defaults(self):
        """Test SOCKS inbound with default parameters."""
        builder = InboundBuilder()
        profile = builder.add_socks().build()
        
        inbound = profile.inbounds[0]
        assert inbound.type == "socks"
        assert inbound.listen == "127.0.0.1"
        assert inbound.port == 1080
        assert inbound.options["tag"] == "socks-in"
        assert "users" not in inbound.options
    
    def test_add_socks_with_auth(self):
        """Test SOCKS inbound with authentication."""
        builder = InboundBuilder()
        profile = builder.add_socks(auth="user:pass", port=1234).build()
        
        inbound = profile.inbounds[0]
        assert inbound.port == 1234
        assert inbound.options["users"] == [{"username": "user", "password": "pass"}]
    
    def test_add_socks_invalid_port(self):
        """Test SOCKS inbound with invalid port."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="Port must be between 1024 and 65535"):
            builder.add_socks(port=80)
    
    def test_add_socks_invalid_auth(self):
        """Test SOCKS inbound with invalid auth format."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="Auth must be in format 'username:password'"):
            builder.add_socks(auth="invalid")
    
    def test_add_http_defaults(self):
        """Test HTTP inbound with default parameters."""
        builder = InboundBuilder()
        profile = builder.add_http().build()
        
        inbound = profile.inbounds[0]
        assert inbound.type == "http"
        assert inbound.listen == "127.0.0.1"
        assert inbound.port == 8080
        assert inbound.options["tag"] == "http-in"
    
    def test_add_http_with_auth(self):
        """Test HTTP inbound with authentication."""
        builder = InboundBuilder()
        profile = builder.add_http(auth="proxy:secret").build()
        
        inbound = profile.inbounds[0]
        assert inbound.options["users"] == [{"username": "proxy", "password": "secret"}]
    
    def test_add_tproxy_defaults(self):
        """Test TPROXY inbound with default parameters."""
        builder = InboundBuilder()
        profile = builder.add_tproxy().build()
        
        inbound = profile.inbounds[0]
        assert inbound.type == "tproxy"
        assert inbound.listen == "0.0.0.0"  # TPROXY needs all interfaces
        assert inbound.port == 7895
        assert inbound.options["tag"] == "tproxy-in"
        assert inbound.options["network"] == "tcp"
    
    def test_add_tproxy_custom_network(self):
        """Test TPROXY inbound with custom network."""
        builder = InboundBuilder()
        profile = builder.add_tproxy(network="tcp,udp").build()
        
        inbound = profile.inbounds[0]
        assert inbound.options["network"] == "tcp,udp"
    
    def test_add_tproxy_invalid_network(self):
        """Test TPROXY inbound with invalid network."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="Invalid network"):
            builder.add_tproxy(network="invalid")
    
    def test_multiple_inbounds(self):
        """Test building profile with multiple inbounds."""
        builder = InboundBuilder()
        profile = (builder
                  .add_tun()
                  .add_socks(port=1080)
                  .add_http(port=8080)
                  .add_tproxy()
                  .build())
        
        assert len(profile.inbounds) == 4
        types = [inbound.type for inbound in profile.inbounds]
        assert "tun" in types
        assert "socks" in types
        assert "http" in types
        assert "tproxy" in types
    
    def test_set_dns_mode(self):
        """Test setting DNS mode."""
        builder = InboundBuilder()
        profile = builder.add_tun().set_dns_mode("tunnel").build()
        
        assert profile.dns_mode == "tunnel"
    
    def test_set_invalid_dns_mode(self):
        """Test setting invalid DNS mode."""
        builder = InboundBuilder()
        with pytest.raises(ValueError, match="Invalid DNS mode"):
            builder.set_dns_mode("invalid")


class TestBuildClientProfileFromCli:
    """Test cases for build_client_profile_from_cli function."""
    
    def test_no_inbound_types_returns_none(self):
        """Test that no inbound types returns None."""
        result = build_client_profile_from_cli()
        assert result is None
    
    def test_single_tun_inbound(self):
        """Test building single TUN inbound."""
        profile = build_client_profile_from_cli(
            inbound_types="tun",
            tun_address="10.0.0.1/24",
            tun_mtu=1400
        )
        
        assert profile is not None
        assert len(profile.inbounds) == 1
        inbound = profile.inbounds[0]
        assert inbound.type == "tun"
        assert inbound.options["address"] == ["10.0.0.1/24"]
        assert inbound.options["mtu"] == 1400
    
    def test_multiple_inbound_types(self):
        """Test building multiple inbound types."""
        profile = build_client_profile_from_cli(
            inbound_types="tun,socks,http",
            socks_port=1080,
            http_port=8080
        )
        
        assert profile is not None
        assert len(profile.inbounds) == 3
        types = [inbound.type for inbound in profile.inbounds]
        assert "tun" in types
        assert "socks" in types
        assert "http" in types
    
    def test_socks_with_auth(self):
        """Test SOCKS inbound with authentication."""
        profile = build_client_profile_from_cli(
            inbound_types="socks",
            socks_auth="user:pass"
        )
        
        inbound = profile.inbounds[0]
        assert inbound.options["users"] == [{"username": "user", "password": "pass"}]
    
    def test_custom_dns_mode(self):
        """Test setting custom DNS mode."""
        profile = build_client_profile_from_cli(
            inbound_types="tun",
            dns_mode="tunnel"
        )
        
        assert profile.dns_mode == "tunnel"
    
    def test_invalid_inbound_type(self):
        """Test invalid inbound type raises error."""
        with pytest.raises(ValueError, match="Unsupported inbound type"):
            build_client_profile_from_cli(inbound_types="invalid")
    
    def test_whitespace_handling(self):
        """Test that whitespace in inbound types is handled correctly."""
        profile = build_client_profile_from_cli(
            inbound_types=" tun , socks , http "
        )
        
        assert len(profile.inbounds) == 3
        types = [inbound.type for inbound in profile.inbounds]
        assert "tun" in types
        assert "socks" in types
        assert "http" in types
    
    def test_case_insensitive_types(self):
        """Test that inbound types are case insensitive."""
        profile = build_client_profile_from_cli(
            inbound_types="TUN,SOCKS,HTTP"
        )
        
        assert len(profile.inbounds) == 3
        types = [inbound.type for inbound in profile.inbounds]
        assert "tun" in types
        assert "socks" in types
        assert "http" in types 