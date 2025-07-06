"""Unit tests for base policy classes."""

from src.sboxmgr.policies.base import BasePolicy, PolicyContext, PolicyResult
from src.sboxmgr.policies.engine import PolicyEngine


class AllowAllPolicy(BasePolicy):
    """Test policy that always allows."""

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return PolicyResult.allow("Always allowed")


class DenyAllPolicy(BasePolicy):
    """Test policy that always denies."""

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return PolicyResult.deny("Always denied")


class CustomNamePolicy(BasePolicy):
    """Test policy with custom name."""

    name = "CustomPolicy"
    description = "Policy with custom name"

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return PolicyResult.allow("Custom policy allowed")


def test_policy_engine_allows():
    """Test that policy engine allows when all policies pass."""
    engine = PolicyEngine()
    engine.register(AllowAllPolicy())
    ctx = PolicyContext()
    result = engine.evaluate(ctx)
    assert result.allowed
    assert result.reason == "All policies passed"


def test_policy_engine_denies():
    """Test that policy engine denies when a policy denies."""
    engine = PolicyEngine()
    engine.register(DenyAllPolicy())
    ctx = PolicyContext()
    result = engine.evaluate(ctx)
    assert not result.allowed
    assert result.reason == "Always denied"
    assert result.policy_name == "DenyAllPolicy"


def test_policy_engine_short_circuit():
    """Test that policy engine stops at first denial."""
    engine = PolicyEngine()
    engine.register(DenyAllPolicy())
    engine.register(AllowAllPolicy())
    ctx = PolicyContext()
    result = engine.evaluate(ctx)
    assert not result.allowed
    assert result.policy_name == "DenyAllPolicy"


def test_policy_result_static_methods():
    """Test PolicyResult static methods."""
    allow_result = PolicyResult.allow("test allow", foo="bar")
    assert allow_result.allowed
    assert allow_result.reason == "test allow"
    assert allow_result.metadata["foo"] == "bar"

    deny_result = PolicyResult.deny("test deny", baz="qux")
    assert not deny_result.allowed
    assert deny_result.reason == "test deny"
    assert deny_result.metadata["baz"] == "qux"


def test_policy_name_auto_detection():
    """Test automatic policy name detection."""
    policy = AllowAllPolicy()
    assert policy.name == "AllowAllPolicy"


def test_policy_custom_name():
    """Test policy with custom name."""
    policy = CustomNamePolicy()
    assert policy.name == "CustomPolicy"


def test_policy_result_metadata():
    """Test PolicyResult metadata handling."""
    res = PolicyResult(
        allowed=True, reason="ok", metadata={"foo": 1}, policy_name="Test"
    )
    assert res.metadata["foo"] == 1
    assert res.policy_name == "Test"
    assert res.allowed


def test_policy_engine_disabled_policy():
    """Test that disabled policies are skipped."""
    engine = PolicyEngine()
    policy = DenyAllPolicy()
    policy.enabled = False
    engine.register(policy)
    engine.register(AllowAllPolicy())

    ctx = PolicyContext()
    result = engine.evaluate(ctx)
    assert result.allowed
    assert result.reason == "All policies passed"
