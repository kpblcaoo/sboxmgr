"""Unit tests for geographic policies."""

from src.sboxmgr.policies.geo_policy import CountryPolicy, ASNPolicy
from src.sboxmgr.policies.base import PolicyContext


class TestCountryPolicy:
    """Test CountryPolicy functionality."""

    def test_no_server_allowed(self):
        """Test that no server is allowed."""
        policy = CountryPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No server to check" in result.reason

    def test_no_country_info_allowed(self):
        """Test that server without country info is allowed."""
        policy = CountryPolicy()
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "No country information available" in result.reason

    def test_whitelist_mode_allowed(self):
        """Test whitelist mode with allowed country."""
        policy = CountryPolicy(allowed_countries=["US", "GB"], mode="whitelist")
        server = {"country": "US", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "US is allowed" in result.reason

    def test_whitelist_mode_denied(self):
        """Test whitelist mode with blocked country."""
        policy = CountryPolicy(allowed_countries=["US", "GB"], mode="whitelist")
        server = {"country": "RU", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "RU not in allowed list" in result.reason
        assert result.metadata["country"] == "RU"
        assert "US" in result.metadata["allowed_countries"]

    def test_blacklist_mode_allowed(self):
        """Test blacklist mode with allowed country."""
        policy = CountryPolicy(blocked_countries=["RU", "CN"], mode="blacklist")
        server = {"country": "US", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "US is allowed" in result.reason

    def test_blacklist_mode_denied(self):
        """Test blacklist mode with blocked country."""
        policy = CountryPolicy(blocked_countries=["RU", "CN"], mode="blacklist")
        server = {"country": "RU", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "RU is blocked" in result.reason
        assert result.metadata["country"] == "RU"

    def test_country_extraction_from_metadata(self):
        """Test country extraction from metadata."""
        policy = CountryPolicy(allowed_countries=["US"])
        server = {"meta": {"country": "US"}, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "US is allowed" in result.reason

    def test_country_extraction_from_attributes(self):
        """Test country extraction from object attributes."""
        class TestServer:
            def __init__(self):
                self.country = "US"
                self.name = "test"
        
        policy = CountryPolicy(allowed_countries=["US"])
        server = TestServer()
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "US is allowed" in result.reason


class TestASNPolicy:
    """Test ASNPolicy functionality."""

    def test_no_server_allowed(self):
        """Test that no server is allowed."""
        policy = ASNPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No server to check" in result.reason

    def test_no_asn_info_allowed(self):
        """Test that server without ASN info is allowed."""
        policy = ASNPolicy()
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "No ASN information available" in result.reason

    def test_whitelist_mode_allowed(self):
        """Test whitelist mode with allowed ASN."""
        policy = ASNPolicy(allowed_asns=[12345, 67890], mode="whitelist")
        server = {"asn": 12345, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "12345 is allowed" in result.reason

    def test_whitelist_mode_denied(self):
        """Test whitelist mode with blocked ASN."""
        policy = ASNPolicy(allowed_asns=[12345, 67890], mode="whitelist")
        server = {"asn": 99999, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "99999 not in allowed list" in result.reason
        assert result.metadata["asn"] == 99999

    def test_blacklist_mode_allowed(self):
        """Test blacklist mode with allowed ASN."""
        policy = ASNPolicy(blocked_asns=[12345, 67890], mode="blacklist")
        server = {"asn": 99999, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "99999 is allowed" in result.reason

    def test_blacklist_mode_denied(self):
        """Test blacklist mode with blocked ASN."""
        policy = ASNPolicy(blocked_asns=[12345, 67890], mode="blacklist")
        server = {"asn": 12345, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "12345 is blocked" in result.reason
        assert result.metadata["asn"] == 12345

    def test_asn_extraction_from_metadata(self):
        """Test ASN extraction from metadata."""
        policy = ASNPolicy(allowed_asns=[12345])
        server = {"meta": {"asn": 12345}, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "12345 is allowed" in result.reason

    def test_asn_extraction_from_attributes(self):
        """Test ASN extraction from object attributes."""
        class TestServer:
            def __init__(self):
                self.asn = 12345
                self.name = "test"
        
        policy = ASNPolicy(allowed_asns=[12345])
        server = TestServer()
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "12345 is allowed" in result.reason

    def test_invalid_asn_handling(self):
        """Test handling of invalid ASN values."""
        policy = ASNPolicy(allowed_asns=[12345])
        server = {"asn": "invalid", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "No ASN information available" in result.reason 