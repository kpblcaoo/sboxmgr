from typing import List, Dict, Any
from src.sboxmgr.subscription.models import ParsedServer
from .routing.default_router import DefaultRouter

class ExportManager:
    def __init__(self, routing_plugin=None):
        self.routing_plugin = routing_plugin or DefaultRouter()

    def export(self, servers: List[ParsedServer], exclusions: List[str] = None, user_routes: List[Dict] = None, context: Dict[str, Any] = None) -> Dict:
        exclusions = exclusions or []
        user_routes = user_routes or []
        context = context or {"mode": "default"}
        # 1. Filter servers by exclusions (assume s.address as unique id)
        filtered_servers = [s for s in servers if s.address not in exclusions]
        # 2. Generate routes
        routes = self.routing_plugin.generate_routes(filtered_servers, exclusions, user_routes, context)
        # 3. Build outbounds
        outbounds = []
        for s in filtered_servers:
            out = {
                "type": s.type,
                "server": s.address,
                "server_port": s.port,
            }
            if s.security:
                out["security"] = s.security
            out.update(s.meta or {})
            outbounds.append(out)
        # 4. Build final config
        config = {
            "outbounds": outbounds,
            "route": {"rules": routes}
        }
        return config 