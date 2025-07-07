"""Profile security policies for sboxmgr.

This module provides policies for validating profile security including
integrity checks, permission validation, and resource limits.
"""

from typing import Optional

from .base import BasePolicy, PolicyContext, PolicyResult


class IntegrityPolicy(BasePolicy):
    """Policy for checking profile integrity.

    Validates that profiles are not corrupted and contain valid data.
    Checks for required fields, data types, and structural integrity.
    """

    name = "IntegrityPolicy"
    description = "Validates profile integrity and data structure"
    group = "profile"

    def __init__(self, required_fields: Optional[list] = None):
        """Initialize integrity policy.

        Args:
            required_fields: List of required fields in profile

        """
        super().__init__()
        self.required_fields = required_fields or ["name", "type"]

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate profile integrity.

        Args:
            context: Context containing profile to validate

        Returns:
            PolicyResult indicating if profile is valid

        """
        profile = context.profile

        if not profile:
            return PolicyResult.allow("No profile to validate")

        # Check if profile is a dict/object
        if not isinstance(profile, dict) and not hasattr(profile, "get"):
            return PolicyResult.deny("Profile must be a dictionary or object")

        # Check required fields (universal getter)
        getter = getattr(profile, "get", lambda x: None)
        for field in self.required_fields:
            if getter(field) is None:
                return PolicyResult.deny(f"Missing required field: {field}")

        return PolicyResult.allow("Profile integrity check passed")


class PermissionPolicy(BasePolicy):
    """Policy for checking profile permissions.

    Validates that the current user has permission to access/modify
    the profile based on ownership and access rules.
    """

    name = "PermissionPolicy"
    description = "Validates profile access permissions"
    group = "profile"

    def __init__(
        self, allowed_users: Optional[list] = None, admin_users: Optional[list] = None
    ):
        """Initialize permission policy.

        Args:
            allowed_users: List of users allowed to access profiles
            admin_users: List of admin users with full access

        """
        super().__init__()
        self.allowed_users = allowed_users or []
        self.admin_users = admin_users or []

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate profile permissions.

        Args:
            context: Context containing user and profile information

        Returns:
            PolicyResult indicating if access is allowed

        """
        user = context.user

        if not user:
            return PolicyResult.allow("No user specified, allowing access")

        # Admin users have full access
        if user in self.admin_users:
            return PolicyResult.allow("Admin user access granted")

        # Check if user is in allowed list
        if self.allowed_users and user not in self.allowed_users:
            return PolicyResult.deny(f"User {user} not in allowed users list")

        return PolicyResult.allow("User permission check passed")


class LimitPolicy(BasePolicy):
    """Policy for enforcing resource limits on profiles.

    Limits the number of servers, subscriptions, and other resources
    that can be included in a profile.
    """

    name = "LimitPolicy"
    description = "Enforces resource limits on profiles"
    group = "profile"

    def __init__(
        self,
        max_servers: int = 1000,
        max_subscriptions: int = 10,
        max_size_mb: int = 10,
    ):
        """Initialize limit policy.

        Args:
            max_servers: Maximum number of servers allowed
            max_subscriptions: Maximum number of subscriptions allowed
            max_size_mb: Maximum profile size in MB

        """
        super().__init__()
        self.max_servers = max_servers
        self.max_subscriptions = max_subscriptions
        self.max_size_mb = max_size_mb

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate resource limits.

        Args:
            context: Context containing profile to check

        Returns:
            PolicyResult indicating if limits are within bounds

        """
        profile = context.profile

        if not profile:
            return PolicyResult.allow("No profile to check limits")

        # Check server count
        if hasattr(profile, "get"):
            servers = profile.get("servers", [])
            if len(servers) > self.max_servers:
                return PolicyResult.deny(
                    f"Too many servers: {len(servers)} > {self.max_servers}",
                    server_count=len(servers),
                    max_servers=self.max_servers,
                )

        # Check subscription count
        if hasattr(profile, "get"):
            subscriptions = profile.get("subscriptions", [])
            if len(subscriptions) > self.max_subscriptions:
                return PolicyResult.deny(
                    f"Too many subscriptions: {len(subscriptions)} > {self.max_subscriptions}",
                    subscription_count=len(subscriptions),
                    max_subscriptions=self.max_subscriptions,
                )

        # Check profile size (rough estimate)
        try:
            import json

            profile_str = json.dumps(profile)
            size_mb = len(profile_str.encode("utf-8")) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                return PolicyResult.deny(
                    f"Profile too large: {size_mb:.2f}MB > {self.max_size_mb}MB",
                    size_mb=size_mb,
                    max_size_mb=self.max_size_mb,
                )
        except Exception as e:
            return PolicyResult.allow("Could not calculate profile size", error=str(e))

        return PolicyResult.allow("Resource limits check passed")
