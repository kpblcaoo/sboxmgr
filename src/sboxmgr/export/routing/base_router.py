"""Base routing plugin interface for generating routing rules.

This module defines the abstract base class for routing plugins that generate
routing rules for different VPN clients. Routing plugins transform server
lists and user preferences into client-specific routing configurations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRoutingPlugin(ABC):
    """Abstract base class for routing rule generators.

    Routing plugins implement client-specific logic for generating routing
    rules that determine how traffic is routed through different proxy servers.
    Each plugin should handle the specific routing rule format and capabilities
    of its target client.
    """

    @abstractmethod
    def generate_routes(
        self,
        servers: List[Any],  # ParsedServer
        exclusions: List[str],
        user_routes: List[Dict],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Generate routing rules for the given servers and configuration.

        Args:
            servers: List of parsed server configurations.
            exclusions: List of server IDs or patterns to exclude from routing.
            user_routes: User-defined routing rules to include.
            context: Additional context information for rule generation.

        Returns:
            List of routing rule dictionaries in the target client format.

        """
        pass
