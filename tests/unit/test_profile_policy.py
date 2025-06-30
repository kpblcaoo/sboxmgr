"""Unit tests for profile security policies."""

import pytest
from src.sboxmgr.policies.profile_policy import IntegrityPolicy, PermissionPolicy, LimitPolicy
from src.sboxmgr.policies.base import PolicyContext


class TestIntegrityPolicy:
    """Test IntegrityPolicy functionality."""

    def test_no_profile_allowed(self):
        """Test that no profile is allowed."""
        policy = IntegrityPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No profile to validate" in result.reason

    def test_valid_profile_passed(self):
        """Test that valid profile passes integrity check."""
        policy = IntegrityPolicy()
        profile = {"name": "test", "type": "singbox"}
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert result.allowed
        assert "integrity check passed" in result.reason

    def test_invalid_profile_denied(self):
        """Test that invalid profile is denied."""
        policy = IntegrityPolicy()
        profile = "not a dict"
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "must be a dictionary" in result.reason

    def test_missing_required_fields(self):
        """Test that missing required fields are detected."""
        policy = IntegrityPolicy(required_fields=["name", "type"])
        profile = {"name": "test"}  # missing type
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Missing required field: type" in result.reason


class TestPermissionPolicy:
    """Test PermissionPolicy functionality."""

    def test_no_user_allowed(self):
        """Test that no user is allowed."""
        policy = PermissionPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No user specified" in result.reason

    def test_admin_user_allowed(self):
        """Test that admin user is allowed."""
        policy = PermissionPolicy(admin_users=["admin"])
        context = PolicyContext(user="admin")
        result = policy.evaluate(context)
        assert result.allowed
        assert "Admin user access granted" in result.reason

    def test_allowed_user_passed(self):
        """Test that allowed user passes."""
        policy = PermissionPolicy(allowed_users=["user1", "user2"])
        context = PolicyContext(user="user1")
        result = policy.evaluate(context)
        assert result.allowed
        assert "permission check passed" in result.reason

    def test_unauthorized_user_denied(self):
        """Test that unauthorized user is denied."""
        policy = PermissionPolicy(allowed_users=["user1", "user2"])
        context = PolicyContext(user="unauthorized")
        result = policy.evaluate(context)
        assert not result.allowed
        assert "not in allowed users list" in result.reason


class TestLimitPolicy:
    """Test LimitPolicy functionality."""

    def test_no_profile_allowed(self):
        """Test that no profile is allowed."""
        policy = LimitPolicy()
        context = PolicyContext()
        result = policy.evaluate(context)
        assert result.allowed
        assert "No profile to check" in result.reason

    def test_within_limits_passed(self):
        """Test that profile within limits passes."""
        policy = LimitPolicy(max_servers=100, max_subscriptions=5)
        profile = {
            "servers": [{"name": f"server{i}"} for i in range(50)],
            "subscriptions": [{"url": f"sub{i}"} for i in range(3)]
        }
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert result.allowed
        assert "limits check passed" in result.reason

    def test_too_many_servers_denied(self):
        """Test that too many servers are denied."""
        policy = LimitPolicy(max_servers=10)
        profile = {
            "servers": [{"name": f"server{i}"} for i in range(15)]
        }
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Too many servers" in result.reason
        assert result.metadata["server_count"] == 15
        assert result.metadata["max_servers"] == 10

    def test_too_many_subscriptions_denied(self):
        """Test that too many subscriptions are denied."""
        policy = LimitPolicy(max_subscriptions=2)
        profile = {
            "subscriptions": [{"url": f"sub{i}"} for i in range(5)]
        }
        context = PolicyContext(profile=profile)
        result = policy.evaluate(context)
        assert not result.allowed
        assert "Too many subscriptions" in result.reason
        assert result.metadata["subscription_count"] == 5
        assert result.metadata["max_subscriptions"] == 2 