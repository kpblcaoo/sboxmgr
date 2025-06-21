from .base_router import BaseRoutingPlugin
from typing import List, Dict, Any

class DefaultRouter(BaseRoutingPlugin):
    def generate_routes(self, servers: List[Any], exclusions: List[str], user_routes: List[Dict], context: Dict[str, Any] = None) -> List[Dict]:
        # For test/demo: log all inputs (could use print or logging)
        print(f"[DefaultRouter] context={context}, exclusions={exclusions}, user_routes={user_routes}")
        return [] 