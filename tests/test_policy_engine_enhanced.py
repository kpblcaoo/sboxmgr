"""Enhanced tests for policy engine with evaluate_all() and PolicyEvaluationResult."""

from unittest.mock import Mock

from sboxmgr.policies.base import (
    BasePolicy,
    PolicyContext,
    PolicyEvaluationResult,
    PolicyResult,
)
from sboxmgr.policies.engine import PolicyEngine


class MockPolicy(BasePolicy):
    """Mock policy for testing."""

    def __init__(self, name="MockPolicy", group="test", result=None):
        super().__init__()
        self.name = name
        self.group = group
        self.description = f"Mock policy {name}"
        self._result = result or PolicyResult.allow("Mock allow")

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return self._result


class TestPolicyEvaluationResult:
    """Test PolicyEvaluationResult class."""

    def test_empty_result(self):
        """Test empty evaluation result."""
        result = PolicyEvaluationResult()
        assert result.is_allowed is True
        assert result.has_denials is False
        assert result.has_warnings is False
        assert len(result.results) == 0
        assert result.overall_reason == "Allowed by all policies"

    def test_single_allow_result(self):
        """Test single allow result."""
        result = PolicyEvaluationResult()
        allow_result = PolicyResult.allow("Test allow")
        result.add_result(allow_result)

        assert result.is_allowed is True
        assert result.has_denials is False
        assert result.has_warnings is False
        assert len(result.results) == 1
        assert len(result.info_results) == 1
        assert result.overall_reason == "Allowed by all policies"

    def test_single_deny_result(self):
        """Test single deny result."""
        result = PolicyEvaluationResult()
        deny_result = PolicyResult.deny("Test deny")
        result.add_result(deny_result)

        assert result.is_allowed is False
        assert result.has_denials is True
        assert result.has_warnings is False
        assert len(result.results) == 1
        assert len(result.denials) == 1
        assert result.overall_reason == "Denied by policies: Test deny"

    def test_single_warning_result(self):
        """Test single warning result."""
        result = PolicyEvaluationResult()
        warning_result = PolicyResult.warning("Test warning")
        result.add_result(warning_result)

        assert result.is_allowed is True
        assert result.has_denials is False
        assert result.has_warnings is True
        assert len(result.results) == 1
        assert len(result.warnings) == 1
        assert result.overall_reason == "Allowed with 1 warning(s)"

    def test_mixed_results(self):
        """Test mixed results (allow, warning, deny)."""
        result = PolicyEvaluationResult()
        result.add_result(PolicyResult.allow("Allow 1"))
        result.add_result(PolicyResult.warning("Warning 1"))
        result.add_result(PolicyResult.deny("Deny 1"))
        result.add_result(PolicyResult.warning("Warning 2"))

        assert result.is_allowed is False
        assert result.has_denials is True
        assert result.has_warnings is True
        assert len(result.denials) == 1
        assert len(result.warnings) == 2
        assert len(result.info_results) == 1
        assert result.overall_reason == "Denied by policies: Deny 1"

    def test_to_dict(self):
        """Test to_dict method."""
        result = PolicyEvaluationResult(server_identifier="test-server")
        result.add_result(PolicyResult.allow("Allow", key="value"))
        result.add_result(PolicyResult.deny("Deny", error="test"))

        data = result.to_dict()
        assert data["server_identifier"] == "test-server"
        assert data["is_allowed"] is False
        assert data["total_policies"] == 2
        assert len(data["denials"]) == 1
        assert len(data["info_results"]) == 1
        assert data["denials"][0]["reason"] == "Deny"
        assert data["denials"][0]["metadata"]["error"] == "test"


class TestPolicyEngineEnhanced:
    """Test enhanced PolicyEngine with evaluate_all()."""

    def setup_method(self):
        """Set up test environment."""
        self.engine = PolicyEngine()
        self.context = PolicyContext(server={"address": "test.com", "type": "vmess"})

    def test_evaluate_all_empty(self):
        """Test evaluate_all with no policies."""
        result = self.engine.evaluate_all(self.context)
        assert result.is_allowed is True
        assert len(result.results) == 0
        assert result.server_identifier == "test.com"

    def test_evaluate_all_single_policy(self):
        """Test evaluate_all with single policy."""
        policy = MockPolicy("TestPolicy", result=PolicyResult.allow("Test"))
        self.engine.register(policy)

        result = self.engine.evaluate_all(self.context)
        assert result.is_allowed is True
        assert len(result.results) == 1
        assert result.results[0].policy_name == "TestPolicy"

    def test_evaluate_all_multiple_policies(self):
        """Test evaluate_all with multiple policies."""
        # Add policies with different results
        self.engine.register(
            MockPolicy("AllowPolicy", result=PolicyResult.allow("Allow"))
        )
        self.engine.register(
            MockPolicy("WarningPolicy", result=PolicyResult.warning("Warning"))
        )
        self.engine.register(MockPolicy("DenyPolicy", result=PolicyResult.deny("Deny")))
        self.engine.register(
            MockPolicy("AllowPolicy2", result=PolicyResult.allow("Allow2"))
        )

        result = self.engine.evaluate_all(self.context)
        assert result.is_allowed is False
        assert len(result.results) == 4
        assert len(result.denials) == 1
        assert len(result.warnings) == 1
        assert len(result.info_results) == 2

    def test_evaluate_all_disabled_policy(self):
        """Test evaluate_all skips disabled policies."""
        policy = MockPolicy(
            "DisabledPolicy", result=PolicyResult.deny("Should not run")
        )
        policy.enabled = False
        self.engine.register(policy)

        result = self.engine.evaluate_all(self.context)
        assert result.is_allowed is True
        assert len(result.results) == 0

    def test_evaluate_all_policy_exception(self):
        """Test evaluate_all handles policy exceptions."""

        class ExceptionPolicy(MockPolicy):
            def evaluate(self, context):
                raise ValueError("Test exception")

        self.engine.register(ExceptionPolicy("ExceptionPolicy"))
        self.engine.register(
            MockPolicy("NormalPolicy", result=PolicyResult.allow("Normal"))
        )

        result = self.engine.evaluate_all(self.context)
        assert result.is_allowed is False
        assert len(result.results) == 2
        assert len(result.denials) == 1
        assert len(result.info_results) == 1

        # Check that exception was handled as denial
        denial = result.denials[0]
        assert "Policy evaluation error" in denial.reason
        assert denial.metadata.get("error_type") == "policy_exception"

    def test_get_policies_filtering(self):
        """Test get_policies with filtering."""
        self.engine.register(MockPolicy("Policy1", group="security"))
        self.engine.register(MockPolicy("Policy2", group="geo"))
        self.engine.register(MockPolicy("Policy3", group="security"))

        # Test group filtering
        security_policies = self.engine.get_policies(group="security")
        assert len(security_policies) == 2
        assert all(p.group == "security" for p in security_policies)

        # Test enabled_only filtering
        disabled_policy = MockPolicy("DisabledPolicy", group="security")
        disabled_policy.enabled = False
        self.engine.register(disabled_policy)

        enabled_policies = self.engine.get_policies(group="security", enabled_only=True)
        assert len(enabled_policies) == 2

        all_policies = self.engine.get_policies(group="security", enabled_only=False)
        assert len(all_policies) == 3

    def test_get_policy(self):
        """Test get_policy method."""
        policy = MockPolicy("TestPolicy")
        self.engine.register(policy)

        found = self.engine.get_policy("TestPolicy")
        assert found is policy

        not_found = self.engine.get_policy("NonExistent")
        assert not_found is None


class TestPolicyContextEnhanced:
    """Test enhanced PolicyContext with get_server_identifier()."""

    def test_get_server_identifier_with_address(self):
        """Test get_server_identifier with address field."""

        class TestServer:
            def __init__(self):
                self.address = "example.com"

        server = TestServer()
        context = PolicyContext(server=server)

        assert context.get_server_identifier() == "example.com"

    def test_get_server_identifier_with_name(self):
        """Test get_server_identifier with name field."""

        class TestServer:
            def __init__(self):
                self.name = "Test Server"

        server = TestServer()
        context = PolicyContext(server=server)

        assert context.get_server_identifier() == "Test Server"

    def test_get_server_identifier_with_tag(self):
        """Test get_server_identifier with tag field."""

        class TestServer:
            def __init__(self):
                self.tag = "US-Server-1"

        server = TestServer()
        context = PolicyContext(server=server)

        assert context.get_server_identifier() == "US-Server-1"

    def test_get_server_identifier_priority(self):
        """Test get_server_identifier priority (address > name > tag)."""

        class TestServer:
            def __init__(self):
                self.address = "example.com"
                self.name = "Test Server"
                self.tag = "US-Server-1"

        server = TestServer()
        context = PolicyContext(server=server)

        assert context.get_server_identifier() == "example.com"

    def test_get_server_identifier_fallback(self):
        """Test get_server_identifier fallback to string representation."""

        class TestServer:
            def __str__(self):
                return "TestServer"

        server = TestServer()
        context = PolicyContext(server=server)

        assert context.get_server_identifier() == "TestServer"

    def test_get_server_identifier_no_server(self):
        """Test get_server_identifier with no server."""
        context = PolicyContext()
        assert context.get_server_identifier() == "unknown"


class TestIntegrationWithSubscriptionManager:
    """Test integration with SubscriptionManager policy application."""

    def test_apply_policies_with_evaluate_all(self):
        """Test that policy application works with real policies (integration test)."""
        from sboxmgr.policies import BasePolicy, PolicyResult, policy_registry
        from sboxmgr.policies import PolicyContext as PolCtx
        from sboxmgr.subscription.models import ParsedServer, PipelineContext

        # Create a real test policy
        class DummyPolicy(BasePolicy):
            name = "DummyPolicy"
            description = "Test policy for integration testing"

            def evaluate(self, context: PolCtx) -> PolicyResult:
                # Allow servers with address "test.com", deny others
                if (
                    hasattr(context.server, "address")
                    and context.server.address == "test.com"
                ):
                    return PolicyResult.allow("Test server allowed")
                else:
                    return PolicyResult.deny("Test server denied")

        # Register the test policy
        test_policy = DummyPolicy()
        original_policies = policy_registry.policies.copy()
        policy_registry.policies = [test_policy]

        try:
            # Create real test servers
            allowed_server = ParsedServer(
                type="vmess", address="test.com", port=443, tag="test-server"
            )
            denied_server = ParsedServer(
                type="vmess", address="blocked.com", port=443, tag="blocked-server"
            )
            servers = [allowed_server, denied_server]

            # Create context
            context = PipelineContext()
            context.metadata = {}

            # Test policy application through pipeline coordinator
            from sboxmgr.subscription.manager import PipelineCoordinator

            coordinator = PipelineCoordinator(
                middleware_chain=Mock(),
                postprocessor=Mock(),
                selector=Mock(),
                error_handler=Mock(),
            )

            result = coordinator.apply_policies(servers, context)

            # Verify that only allowed server passed through
            assert len(result) == 1
            assert result[0].address == "test.com"

        finally:
            # Restore original policies
            policy_registry.policies = original_policies

    def test_apply_policies_fail_tolerant(self):
        """Test that pipeline does not crash in fail-tolerant mode and error is recorded."""
        from sboxmgr.policies import BasePolicy, PolicyResult, policy_registry
        from sboxmgr.policies import PolicyContext as PolCtx
        from sboxmgr.subscription.models import ParsedServer, PipelineContext

        class FailingPolicy(BasePolicy):
            name = "FailingPolicy"
            description = "Policy that always raises an exception"

            def evaluate(self, context: PolCtx) -> PolicyResult:
                raise RuntimeError("Intentional policy failure")

        test_policy = FailingPolicy()
        original_policies = policy_registry.policies.copy()
        policy_registry.policies = [test_policy]
        try:
            servers = [
                ParsedServer(
                    type="vmess", address="test.com", port=443, tag="test-server"
                )
            ]
            context = PipelineContext()
            context.metadata = {}
            context.fail_tolerant = True
            from sboxmgr.subscription.manager import PipelineCoordinator

            coordinator = PipelineCoordinator(
                middleware_chain=None,
                postprocessor=None,
                selector=None,
                error_handler=None,
            )
            result = coordinator.apply_policies(servers, context)
            assert result == servers  # pipeline не фильтрует
            assert "policy_error" in context.metadata
            assert hasattr(context, "flags") and "policy_error" in context.flags
        finally:
            policy_registry.policies = original_policies

    def test_apply_policies_strict_mode_crash(self):
        """Test that pipeline crashes in strict mode if policy fails."""
        from sboxmgr.policies import BasePolicy, PolicyResult, policy_registry
        from sboxmgr.policies import PolicyContext as PolCtx
        from sboxmgr.subscription.models import ParsedServer, PipelineContext

        class FailingPolicy(BasePolicy):
            name = "FailingPolicy"
            description = "Policy that always raises an exception"

            def evaluate(self, context: PolCtx) -> PolicyResult:
                raise RuntimeError("Intentional policy failure")

        test_policy = FailingPolicy()
        original_policies = policy_registry.policies.copy()
        policy_registry.policies = [test_policy]
        try:
            servers = [
                ParsedServer(
                    type="vmess", address="test.com", port=443, tag="test-server"
                )
            ]
            context = PipelineContext()
            context.metadata = {}
            # fail_tolerant не установлен
            from sboxmgr.subscription.manager import PipelineCoordinator

            coordinator = PipelineCoordinator(
                middleware_chain=None,
                postprocessor=None,
                selector=None,
                error_handler=None,
            )
            import pytest

            with pytest.raises(RuntimeError, match="Intentional policy failure"):
                coordinator.apply_policies(servers, context)
        finally:
            policy_registry.policies = original_policies
