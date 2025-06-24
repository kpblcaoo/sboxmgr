from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRoutingPlugin(ABC):
    @abstractmethod
    def generate_routes(
        self,
        servers: List[Any],  # ParsedServer
        exclusions: List[str],
        user_routes: List[Dict],
        context: Dict[str, Any] = None
    ) -> List[Dict]:
        """
        Generate routing rules for given servers.
        context['mode'] (str) is required for plugin customization.
        """
        pass 