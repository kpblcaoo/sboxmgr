from src.sboxmgr.export.export_manager import ExportManager
from src.sboxmgr.export.routing.default_router import DefaultRouter
from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
from src.sboxmgr.subscription.models import ParsedServer

class TestRouter(BaseRoutingPlugin):
    def __init__(self):
        self.last_call = None
    def generate_routes(self, servers, exclusions, user_routes, context=None):
        self.last_call = {
            'servers': servers,
            'exclusions': exclusions,
            'user_routes': user_routes,
            'context': context,
        }
        return [{"test": True}]

def test_default_router_returns_list():
    router = DefaultRouter()
    servers = []
    routes = router.generate_routes(servers, [], [], context={"mode": "default"})
    assert isinstance(routes, list)

def test_export_manager_with_test_router():
    router = TestRouter()
    servers = [ParsedServer(type="ss", address="1.2.3.4", port=1234, security=None, meta={"tag": "test"})]
    exclusions = ["5.6.7.8"]
    user_routes = [{"domain": ["example.com"], "outbound": "ss"}]
    context = {"mode": "geo", "custom": 42}
    mgr = ExportManager(routing_plugin=router)
    config = mgr.export(servers, exclusions, user_routes, context)
    assert config["route"]["rules"] == [{"test": True}]
    assert router.last_call["context"]["mode"] == "geo"
    assert router.last_call["user_routes"] == user_routes
    assert router.last_call["servers"] == servers 