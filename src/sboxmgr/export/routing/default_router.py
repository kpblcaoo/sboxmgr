from .base_router import BaseRoutingPlugin
from typing import List, Dict, Any

class DefaultRouter(BaseRoutingPlugin):
    def generate_routes(self, servers: List[Any], exclusions: List[str], user_routes: List[Dict], context: Dict[str, Any] = None) -> List[Dict]:
        # Логируем только при debug_level >= 2
        debug_level = getattr(context, 'debug_level', 0) if context else 0
        if debug_level >= 2:
            print(f"[DefaultRouter] context={context}, exclusions={exclusions}, user_routes={user_routes}")
        return [] 