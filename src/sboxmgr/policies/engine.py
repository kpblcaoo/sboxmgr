"""Policy engine for evaluating policies.

This module provides the PolicyEngine class which manages and evaluates
a collection of policies against given contexts.
"""

import logging

from .base import BasePolicy, PolicyContext, PolicyEvaluationResult, PolicyResult


class PolicyEngine:
    """Engine for evaluating multiple policies.

    The PolicyEngine maintains a list of policies and evaluates them
    in order until one denies the action or all policies pass.

    Attributes:
        policies: List of registered policies
        logger: Logger for policy evaluation events

    """

    def __init__(self):
        """Initialize the policy engine."""
        self.policies: list[BasePolicy] = []
        self.logger = logging.getLogger(__name__)

    def register(self, policy: BasePolicy) -> None:
        """Register a policy with the engine.

        Args:
            policy: Policy to register

        """
        self.policies.append(policy)
        self.logger.debug(f"Registered policy: {policy.name}")

    def enable(self, name: str) -> bool:
        """Enable a policy by name.

        Args:
            name: Name of the policy to enable
        Returns:
            True if found and enabled, False otherwise

        """
        for p in self.policies:
            if p.name == name:
                p.enabled = True
                return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a policy by name.

        Args:
            name: Name of the policy to disable
        Returns:
            True if found and disabled, False otherwise

        """
        for p in self.policies:
            if p.name == name:
                p.enabled = False
                return True
        return False

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate policies until first denial or all pass.

        This method evaluates policies in order and returns the first
        denial result or allows if all policies pass.

        Args:
            context: Context to evaluate against

        Returns:
            PolicyResult from first denying policy or allow result

        """
        for policy in self.policies:
            if not policy.enabled:
                self.logger.debug(f"Skipping disabled policy: {policy.name}")
                continue

            result = policy.evaluate(context)
            result.policy_name = getattr(policy, "name", policy.__class__.__name__)

            if not result.allowed:
                self.logger.info(f"Policy {result.policy_name} denied: {result.reason}")
                return result

        return PolicyResult.allow("All policies passed")

    def evaluate_all(self, context: PolicyContext) -> PolicyEvaluationResult:
        """Evaluate all policies and return aggregated results.

        This method evaluates all enabled policies and collects their
        results, providing detailed information about all decisions.

        Args:
            context: Context to evaluate against

        Returns:
            PolicyEvaluationResult containing all policy results

        """
        evaluation_result = PolicyEvaluationResult(
            server_identifier=context.get_server_identifier()
        )

        for policy in self.policies:
            if not policy.enabled:
                self.logger.debug(f"Skipping disabled policy: {policy.name}")
                continue

            try:
                result = policy.evaluate(context)
                result.policy_name = getattr(policy, "name", policy.__class__.__name__)
                evaluation_result.add_result(result)

                self.logger.debug(
                    f"Policy {result.policy_name}: {result.severity.value} - {result.reason}"
                )

            except Exception as e:
                # Fail-secure: treat policy errors as denials
                error_result = PolicyResult.deny(
                    f"Policy evaluation error: {e}",
                    error_type="policy_exception",
                    policy_name=getattr(policy, "name", policy.__class__.__name__),
                )
                evaluation_result.add_result(error_result)
                self.logger.error(f"Policy {policy.name} evaluation failed: {e}")

        # Log summary
        if evaluation_result.has_denials:
            self.logger.info(
                f"Server {evaluation_result.server_identifier} denied by {len(evaluation_result.denials)} policy(ies)"
            )
        elif evaluation_result.has_warnings:
            self.logger.info(
                f"Server {evaluation_result.server_identifier} allowed with {len(evaluation_result.warnings)} warning(s)"
            )
        else:
            self.logger.debug(
                f"Server {evaluation_result.server_identifier} allowed by all policies"
            )

        return evaluation_result

    def get_policies(
        self, group: str = None, enabled_only: bool = True
    ) -> list[BasePolicy]:
        """Get policies with optional filtering.

        Args:
            group: Optional group filter
            enabled_only: Whether to return only enabled policies

        Returns:
            List of matching policies

        """
        result = []
        for policy in self.policies:
            if enabled_only and not policy.enabled:
                continue
            if group and policy.group != group:
                continue
            result.append(policy)
        return result

    def get_policy(self, name: str) -> BasePolicy:
        """Get a specific policy by name.

        Args:
            name: Name of the policy to find

        Returns:
            Policy object or None if not found

        """
        for policy in self.policies:
            if policy.name == name:
                return policy
        return None
