"""Tests for smart export functionality of sing-box models."""

from src.sboxmgr.models.singbox.common import TransportConfig
from src.sboxmgr.models.singbox.inbounds import MixedInbound, SocksInbound, VmessInbound
from src.sboxmgr.models.singbox.outbounds import (
    BlockOutbound,
    DirectOutbound,
    DnsOutbound,
    VmessOutbound,
)


class TestSmartExport:
    """Test smart export functionality."""

    def test_block_outbound_smart_export(self):
        """Test that BlockOutbound removes unsupported fields."""
        block = BlockOutbound(tag="block-tag")

        # Standard export should include all fields from OutboundBase
        standard_data = block.model_dump()
        assert "server" in standard_data
        assert "server_port" in standard_data
        # Note: tls is not in OutboundBase anymore, only in OutboundWithTls
        # Note: transport is not inherited by BlockOutbound, so it won't be in standard_data

        # Smart export should remove unsupported fields
        smart_data = block.smart_dump(exclude_unset=False)
        assert "server" not in smart_data
        assert "server_port" not in smart_data
        assert "tls" not in smart_data
        assert "transport" not in smart_data
        assert smart_data["type"] == "block"
        assert smart_data["tag"] == "block-tag"

    def test_direct_outbound_smart_export(self):
        """Test that DirectOutbound removes unsupported fields."""
        direct = DirectOutbound(tag="direct-tag", server="1.2.3.4", server_port=1080)

        # Standard export should include all fields from OutboundBase
        standard_data = direct.model_dump()
        # Note: tls is not in OutboundBase anymore, only in OutboundWithTls
        # Note: transport is not inherited by DirectOutbound, so it won't be in standard_data

        # Smart export should remove unsupported fields
        smart_data = direct.smart_dump(exclude_unset=False)
        assert "tls" not in smart_data
        assert "transport" not in smart_data
        assert smart_data["type"] == "direct"
        assert smart_data["server"] == "1.2.3.4"
        assert smart_data["server_port"] == 1080

    def test_dns_outbound_smart_export(self):
        """Test that DnsOutbound removes unsupported fields."""
        dns = DnsOutbound(tag="dns-tag")

        # Standard export should include all fields from OutboundBase
        standard_data = dns.model_dump()
        assert "server" in standard_data
        assert "server_port" in standard_data
        # Note: tls is not in OutboundBase anymore, only in OutboundWithTls
        # Note: transport is not inherited by DnsOutbound, so it won't be in standard_data

        # Smart export should remove unsupported fields
        smart_data = dns.smart_dump(exclude_unset=False)
        assert "server" not in smart_data
        assert "transport" not in smart_data
        assert smart_data["type"] == "dns"

    def test_vmess_outbound_smart_export(self):
        """Test that VmessOutbound keeps supported fields."""
        transport = TransportConfig(type="ws", path="/ws")
        vmess = VmessOutbound(
            tag="vmess-tag",
            server="1.2.3.4",
            server_port=1080,
            uuid="test-uuid",
            transport=transport,
        )

        # Smart export should keep transport (supported by VMess)
        smart_data = vmess.smart_dump(exclude_unset=False)
        assert smart_data["type"] == "vmess"
        assert smart_data["transport"]["type"] == "ws"
        assert smart_data["transport"]["path"] == "/ws"
        assert smart_data["server"] == "1.2.3.4"
        assert smart_data["server_port"] == 1080

    def test_mixed_inbound_smart_export(self):
        """Test that MixedInbound removes unsupported fields."""
        mixed = MixedInbound(tag="mixed-tag", listen="0.0.0.0", listen_port=1080)

        # Standard export should not include transport (not inherited)
        standard_data = mixed.model_dump()
        assert "transport" not in standard_data

        # Smart export should not have transport (not supported by mixed)
        smart_data = mixed.smart_dump(exclude_unset=False)
        assert "transport" not in smart_data
        assert smart_data["type"] == "mixed"
        assert smart_data["listen"] == "0.0.0.0"
        assert smart_data["listen_port"] == 1080

    def test_socks_inbound_smart_export(self):
        """Test that SocksInbound removes unsupported fields."""
        socks = SocksInbound(tag="socks-tag", listen="0.0.0.0", listen_port=1080)

        # Standard export should not include transport (not inherited)
        standard_data = socks.model_dump()
        assert "transport" not in standard_data

        # Smart export should not have transport (not supported by SOCKS)
        smart_data = socks.smart_dump(exclude_unset=False)
        assert "transport" not in smart_data
        assert smart_data["type"] == "socks"
        assert smart_data["listen"] == "0.0.0.0"
        assert smart_data["listen_port"] == 1080

    def test_vmess_inbound_smart_export(self):
        """Test that VmessInbound keeps supported fields."""
        transport = TransportConfig(type="ws", path="/ws")
        vmess = VmessInbound(
            tag="vmess-tag", listen="0.0.0.0", listen_port=1080, transport=transport
        )

        # Smart export should keep transport (supported by VMess)
        smart_data = vmess.smart_dump(exclude_unset=False)
        assert smart_data["type"] == "vmess"
        assert smart_data["transport"]["type"] == "ws"
        assert smart_data["transport"]["path"] == "/ws"
        assert smart_data["listen"] == "0.0.0.0"
        assert smart_data["listen_port"] == 1080

    def test_exclude_unset_and_none(self):
        """Test exclude_unset and exclude_none parameters."""
        vmess = VmessOutbound(
            tag="vmess-tag", server="1.2.3.4", server_port=1080, uuid="test-uuid"
        )

        # Test exclude_unset=True, exclude_none=True (default)
        smart_data = vmess.smart_dump()
        assert "tls" not in smart_data  # Should be excluded as None
        assert "multiplex" not in smart_data  # Should be excluded as None

        # Test exclude_unset=False, exclude_none=False
        smart_data_full = vmess.smart_dump(exclude_unset=False, exclude_none=False)
        assert "tls" in smart_data_full  # Should be included even if None
        assert "multiplex" in smart_data_full  # Should be included even if None
        assert smart_data_full["tls"] is None
        assert smart_data_full["multiplex"] is None
