"""Policy system for sboxmgr.

This module provides the policy system including the global policy registry
and base classes for implementing custom policies.
"""

from .base import (
    BasePolicy,
    PolicyContext,
    PolicyEvaluationResult,
    PolicyResult,
    PolicySeverity,
)
from .engine import PolicyEngine
from .geo_policy import ASNPolicy, CountryPolicy
from .geo_test_policy import GeoTestPolicy
from .profile_policy import IntegrityPolicy, LimitPolicy, PermissionPolicy
from .security_policy import AuthenticationPolicy, EncryptionPolicy, ProtocolPolicy

# Global policy registry for easy access
policy_registry = PolicyEngine()

# Register demo policies
policy_registry.register(GeoTestPolicy())

# Register profile security policies
policy_registry.register(IntegrityPolicy())
policy_registry.register(
    PermissionPolicy(allowed_users=["test"], admin_users=["admin"])
)
policy_registry.register(LimitPolicy(max_servers=1000))

# Register geographic policies
policy_registry.register(CountryPolicy(allowed_countries=["US", "GB", "DE", "NL"]))
policy_registry.register(ASNPolicy(blocked_asns=[12345, 67890], mode="blacklist"))

# Register security policies
policy_registry.register(ProtocolPolicy())
policy_registry.register(EncryptionPolicy())
policy_registry.register(AuthenticationPolicy())

__all__ = [
    "BasePolicy",
    "PolicyContext",
    "PolicyResult",
    "PolicySeverity",
    "PolicyEvaluationResult",
    "PolicyEngine",
    "policy_registry",
    "IntegrityPolicy",
    "PermissionPolicy",
    "LimitPolicy",
    "CountryPolicy",
    "ASNPolicy",
    "ProtocolPolicy",
    "EncryptionPolicy",
    "AuthenticationPolicy",
]
