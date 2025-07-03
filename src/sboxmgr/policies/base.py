"""Base classes for policy system.

This module provides the foundation for the policy system including
PolicyContext, PolicyResult, and BasePolicy classes.
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from enum import Enum

class PolicySeverity(Enum):
    """Policy severity levels."""
    WARNING = "warning"
    DENY = "deny"
    INFO = "info"

@dataclass
class PolicyResult:
    """Result of policy evaluation.
    
    Attributes:
        allowed: Whether the policy allows the action
        reason: Human-readable reason for the decision
        metadata: Additional metadata about the decision
        policy_name: Name of the policy that made the decision
        timestamp: When the decision was made
        severity: Severity level of the decision
    """
    allowed: bool
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    policy_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    severity: PolicySeverity = PolicySeverity.DENY

    @staticmethod
    def allow(reason: str = "Allowed", **metadata) -> "PolicyResult":
        """Create an allowed policy result.
        
        Args:
            reason: Human-readable reason for allowing
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=True
        """
        return PolicyResult(allowed=True, reason=reason, metadata=metadata, severity=PolicySeverity.INFO)

    @staticmethod
    def deny(reason: str, **metadata) -> "PolicyResult":
        """Create a denied policy result.
        
        Args:
            reason: Human-readable reason for denying
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=False
        """
        return PolicyResult(allowed=False, reason=reason, metadata=metadata, severity=PolicySeverity.DENY)

    @staticmethod
    def warning(reason: str, **metadata) -> "PolicyResult":
        """Create a warning policy result.
        
        Args:
            reason: Human-readable warning message
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=True but warning severity
        """
        return PolicyResult(allowed=True, reason=reason, metadata=metadata, severity=PolicySeverity.WARNING)

@dataclass
class PolicyEvaluationResult:
    """Aggregated result of multiple policy evaluations.
    
    This class collects all policy results for a single evaluation
    and provides methods to determine the overall outcome.
    
    Attributes:
        results: List of all policy results
        server_identifier: Identifier for the server being evaluated
    """
    results: List[PolicyResult] = field(default_factory=list)
    server_identifier: str = ""
    
    def add_result(self, result: PolicyResult) -> None:
        """Add a policy result to the collection.
        
        Args:
            result: Policy result to add
        """
        self.results.append(result)
    
    @property
    def has_denials(self) -> bool:
        """Check if any policy denied the action.
        
        Returns:
            True if any policy result has severity DENY
        """
        return any(r.severity == PolicySeverity.DENY for r in self.results)
    
    @property
    def has_warnings(self) -> bool:
        """Check if any policy issued warnings.
        
        Returns:
            True if any policy result has severity WARNING
        """
        return any(r.severity == PolicySeverity.WARNING for r in self.results)
    
    @property
    def denials(self) -> List[PolicyResult]:
        """Get all denial results.
        
        Returns:
            List of policy results with DENY severity
        """
        return [r for r in self.results if r.severity == PolicySeverity.DENY]
    
    @property
    def warnings(self) -> List[PolicyResult]:
        """Get all warning results.
        
        Returns:
            List of policy results with WARNING severity
        """
        return [r for r in self.results if r.severity == PolicySeverity.WARNING]
    
    @property
    def info_results(self) -> List[PolicyResult]:
        """Get all info results.
        
        Returns:
            List of policy results with INFO severity
        """
        return [r for r in self.results if r.severity == PolicySeverity.INFO]
    
    @property
    def is_allowed(self) -> bool:
        """Determine if the action is allowed based on all results.
        
        Returns:
            True if no policies denied the action
        """
        return not self.has_denials
    
    @property
    def overall_reason(self) -> str:
        """Get a summary reason for the overall decision.
        
        Returns:
            Human-readable summary of the evaluation
        """
        if self.has_denials:
            denial_reasons = [r.reason for r in self.denials]
            return f"Denied by policies: {'; '.join(denial_reasons)}"
        elif self.has_warnings:
            warning_count = len(self.warnings)
            return f"Allowed with {warning_count} warning(s)"
        else:
            return "Allowed by all policies"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the evaluation result
        """
        return {
            "server_identifier": self.server_identifier,
            "is_allowed": self.is_allowed,
            "overall_reason": self.overall_reason,
            "denials": [{"policy": r.policy_name, "reason": r.reason, "metadata": r.metadata} for r in self.denials],
            "warnings": [{"policy": r.policy_name, "reason": r.reason, "metadata": r.metadata} for r in self.warnings],
            "info_results": [{"policy": r.policy_name, "reason": r.reason, "metadata": r.metadata} for r in self.info_results],
            "total_policies": len(self.results)
        }

@dataclass
class PolicyContext:
    """Context for policy evaluation.
    
    Attributes:
        profile: Profile being evaluated
        server: Server being evaluated
        user: User making the request
        location: Geographic location information
        env: Environment variables
        metadata: Additional context metadata
    """
    profile: Optional[Any] = None
    server: Optional[Any] = None
    user: Optional[str] = None
    location: Optional[Any] = None
    env: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_server_identifier(self) -> str:
        """Get a consistent identifier for the server being evaluated.
        
        Returns:
            Server identifier (address, name, or string representation)
        """
        if not self.server:
            return "unknown"
        
        # Handle dictionary objects
        if isinstance(self.server, dict):
            if 'address' in self.server:
                return str(self.server['address'])
            if 'name' in self.server:
                return str(self.server['name'])
            if 'tag' in self.server:
                return str(self.server['tag'])
            return str(self.server)
        
        # Handle object attributes
        address = getattr(self.server, 'address', None)
        if address is not None:
            return str(address)
        
        name = getattr(self.server, 'name', None)
        if name is not None:
            return str(name)
        
        tag = getattr(self.server, 'tag', None)
        if tag is not None:
            return str(tag)
        
        # Fallback to string representation
        return str(self.server)

class BasePolicy(ABC):
    """Base class for all policies.
    
    All policies must inherit from this class and implement the evaluate method.
    Policies should be deterministic and not have side effects.
    
    Attributes:
        name: Human-readable name of the policy
        description: Description of what the policy does
        enabled: Whether the policy is currently enabled
        group: Group/category of the policy (e.g., 'profile', 'geo', 'security')
    """
    name: str = "BasePolicy"
    description: str = "Base policy class"
    enabled: bool = True
    group: str = "default"

    def __init__(self):
        """Initialize the policy with automatic name detection."""
        if self.name == "BasePolicy":
            self.name = self.__class__.__name__

    def __repr__(self) -> str:
        """String representation for CLI display."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name}({self.group}, {status})"

    def allow(self, reason: str = "Allowed", **metadata) -> PolicyResult:
        """Create an allowed result for this policy.
        
        Args:
            reason: Human-readable reason for allowing
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=True
        """
        return PolicyResult.allow(reason, **metadata)

    def deny(self, reason: str, **metadata) -> PolicyResult:
        """Create a denied result for this policy.
        
        Args:
            reason: Human-readable reason for denying
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=False
        """
        return PolicyResult.deny(reason, **metadata)

    def warning(self, reason: str, **metadata) -> PolicyResult:
        """Create a warning result for this policy.
        
        Args:
            reason: Human-readable warning message
            **metadata: Additional metadata
            
        Returns:
            PolicyResult with allowed=True but warning severity
        """
        return PolicyResult.warning(reason, **metadata)

    @abstractmethod
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        """Evaluate the policy against the given context.
        
        Args:
            context: Context to evaluate against
            
        Returns:
            PolicyResult indicating whether the action is allowed
        """
        raise NotImplementedError

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate policy configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        return True 