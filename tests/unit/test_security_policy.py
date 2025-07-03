"""Unit tests for security policies."""

from src.sboxmgr.policies.security_policy import ProtocolPolicy, EncryptionPolicy, AuthenticationPolicy
from src.sboxmgr.policies.base import PolicyContext


class TestProtocolPolicy:
    """Test ProtocolPolicy functionality."""

    def test_no_server_allowed(self):
        """Test that no server is allowed."""
        policy = ProtocolPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No server to check" in result.reason

    def test_no_protocol_info_allowed(self):
        """Test that server without protocol info is allowed."""
        policy = ProtocolPolicy()
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "No protocol information available" in result.reason

    def test_whitelist_mode_allowed(self):
        """Test whitelist mode with allowed protocol."""
        policy = ProtocolPolicy(allowed_protocols=["vless", "trojan"])
        server = {"protocol": "vless", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "vless is allowed" in result.reason

    def test_whitelist_mode_denied(self):
        """Test whitelist mode with blocked protocol."""
        policy = ProtocolPolicy(allowed_protocols=["vless", "trojan"])
        server = {"protocol": "http", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "http not in allowed list" in result.reason
        assert result.metadata["protocol"] == "http"

    def test_blacklist_mode_allowed(self):
        """Test blacklist mode with allowed protocol."""
        policy = ProtocolPolicy(blocked_protocols=["http", "socks4"], mode="blacklist")
        server = {"protocol": "vless", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "vless is allowed" in result.reason

    def test_blacklist_mode_denied(self):
        """Test blacklist mode with blocked protocol."""
        policy = ProtocolPolicy(blocked_protocols=["http", "socks4"], mode="blacklist")
        server = {"protocol": "http", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "http is blocked" in result.reason

    def test_protocol_extraction_from_metadata(self):
        """Test protocol extraction from metadata."""
        policy = ProtocolPolicy(allowed_protocols=["vless"])
        server = {"meta": {"protocol": "vless"}, "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "vless is allowed" in result.reason


class TestEncryptionPolicy:
    """Test EncryptionPolicy functionality."""

    def test_no_server_allowed(self):
        """Test that no server is allowed."""
        policy = EncryptionPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No server to check" in result.reason

    def test_no_encryption_required(self):
        """Test that no encryption is allowed when not required."""
        policy = EncryptionPolicy(require_encryption=False)
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "not required" in result.reason

    def test_encryption_required_denied(self):
        """Test that missing encryption is denied when required."""
        policy = EncryptionPolicy(require_encryption=True)
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Encryption is required" in result.reason

    def test_strong_encryption_allowed(self):
        """Test that strong encryption is allowed."""
        policy = EncryptionPolicy()
        server = {"encryption": "tls", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "Strong encryption" in result.reason

    def test_weak_encryption_denied(self):
        """Test that weak encryption is denied."""
        policy = EncryptionPolicy()
        server = {"encryption": "none", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Weak encryption method" in result.reason
        assert result.metadata["encryption"] == "none"

    def test_unknown_encryption_allowed(self):
        """Test that unknown encryption is allowed."""
        policy = EncryptionPolicy()
        server = {"encryption": "custom-method", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "Unknown encryption method" in result.reason


class TestAuthenticationPolicy:
    """Test AuthenticationPolicy functionality."""

    def test_no_server_allowed(self):
        """Test that no server is allowed."""
        policy = AuthenticationPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No server to check" in result.reason

    def test_no_auth_required(self):
        """Test that no authentication is allowed when not required."""
        policy = AuthenticationPolicy(required_auth=False)
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "not required" in result.reason

    def test_auth_required_denied(self):
        """Test that missing authentication is denied when required."""
        policy = AuthenticationPolicy(required_auth=True)
        server = {"name": "test", "port": 443}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Authentication is required" in result.reason

    def test_valid_auth_method_allowed(self):
        """Test that valid authentication method is allowed."""
        policy = AuthenticationPolicy(allowed_auth_methods=["password", "uuid"])
        server = {"auth_method": "password", "password": "secret123", "name": "test"}  # pragma: allowlist secret
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "requirements met" in result.reason

    def test_invalid_auth_method_denied(self):
        """Test that invalid authentication method is denied."""
        policy = AuthenticationPolicy(allowed_auth_methods=["password", "uuid"])
        server = {"auth_method": "weak_auth", "name": "test"}
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "not allowed" in result.reason
        assert result.metadata["auth_method"] == "weak_auth"

    def test_short_password_denied(self):
        """Test that short password is denied."""
        policy = AuthenticationPolicy(min_password_length=10)
        server = {"password": "short", "name": "test"}  # pragma: allowlist secret
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "too short" in result.reason
        assert result.metadata["credential_length"] == 5
        assert result.metadata["min_length"] == 10

    def test_long_password_allowed(self):
        """Test that long password is allowed."""
        policy = AuthenticationPolicy(min_password_length=5)
        server = {"password": "very_long_password_123", "name": "test"}  # pragma: allowlist secret
        context = PolicyContext(server=server)
        result = policy.evaluate(context)
        assert result.allowed
        assert "requirements met" in result.reason 