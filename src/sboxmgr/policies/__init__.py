"""Policy system for sboxmgr.

This module provides the policy system including the global policy registry
and base classes for implementing custom policies.
"""

from .base import BasePolicy, PolicyContext, PolicyResult, PolicySeverity, PolicyEvaluationResult
from .engine import PolicyEngine

# Global policy registry for easy access
policy_registry = PolicyEngine()

# Register demo policies
from .geo_test_policy import GeoTestPolicy
policy_registry.register(GeoTestPolicy())

# Register profile security policies
from .profile_policy import IntegrityPolicy, PermissionPolicy, LimitPolicy
policy_registry.register(IntegrityPolicy())
policy_registry.register(PermissionPolicy(allowed_users=["test"], admin_users=["admin"]))
policy_registry.register(LimitPolicy(max_servers=1000))

# Register geographic policies
from .geo_policy import CountryPolicy, ASNPolicy
policy_registry.register(CountryPolicy(allowed_countries=["US", "GB", "DE", "NL"]))
policy_registry.register(ASNPolicy(blocked_asns=[12345, 67890], mode="blacklist"))

# Register security policies
from .security_policy import ProtocolPolicy, EncryptionPolicy, AuthenticationPolicy
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