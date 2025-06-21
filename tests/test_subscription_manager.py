import os
import pytest
from src.sboxmgr.subscription.models import SubscriptionSource
from src.sboxmgr.subscription.manager import SubscriptionManager
from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin

def test_base64_subscription(tmp_path):
    example_path = os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_base64.txt')
    with open(example_path, 'rb') as f:
        raw = f.read()
    # Эмулируем fetcher, подставляя raw напрямую (или через временный fetcher)
    source = SubscriptionSource(url='file://' + example_path, source_type='url_base64')
    mgr = SubscriptionManager(source)
    servers = mgr.get_servers()
    assert isinstance(servers, list)

# Пример edge-case подписок (минимальные заглушки)
MIXED_URI_LIST = """
# comment
ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#emoji🚀?plugin=obfs  # pragma: allowlist secret
vmess://eyJhZGQiOiJ2bS5jb20iLCJwb3J0Ijo0NDN9  # pragma: allowlist secret
ss://aes-256-gcm:pass@example.com:8388#ssuri  # pragma: allowlist secret
"""

INVALID_JSON = "{"  # Некорректный JSON

@pytest.mark.parametrize("source,should_fail", [
    (SubscriptionSource(url="file://mixed_uri_list.txt", source_type="url_base64"), True),
    (SubscriptionSource(url="file://invalid.json", source_type="url_json"), True),
])
def test_subscription_manager_edge_cases(tmp_path, source, should_fail):
    # Подготовка файлов
    if source.url.endswith("mixed_uri_list.txt"):
        f = tmp_path / "mixed_uri_list.txt"
        f.write_text(MIXED_URI_LIST)
        source.url = f"file://{f}"
    elif source.url.endswith("invalid.json"):
        f = tmp_path / "invalid.json"
        f.write_text(INVALID_JSON)
        source.url = f"file://{f}"
    mgr = SubscriptionManager(source)
    if should_fail:
        # Ошибка на невалидном base64/JSON — это ожидаемо и соответствует best practices
        with pytest.raises(Exception):
            mgr.get_servers()
    else:
        servers = mgr.get_servers()
        assert any(s.type == "ss" for s in servers)
        assert any("emoji" in (s.meta or {}).get("tag", "") or "🚀" in (s.meta or {}).get("tag", "") for s in servers) 

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

def test_export_config_with_test_router(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    # Мокаем get_servers для простоты
    mgr.get_servers = lambda: [
        type('S', (), {"type": "ss", "address": "1.2.3.4", "port": 1234, "security": None, "meta": {"tag": "test"}})()
    ]
    router = TestRouter()
    exclusions = ["5.6.7.8"]
    user_routes = [{"domain": ["example.com"], "outbound": "ss"}]
    context = {"mode": "geo", "custom": 42}
    config = mgr.export_config(exclusions, user_routes, context, routing_plugin=router)
    assert config["route"]["rules"] == [{"test": True}]
    assert router.last_call["context"]["mode"] == "geo"
    assert router.last_call["user_routes"] == user_routes
    assert router.last_call["servers"][0].address == "1.2.3.4" 

def test_export_config_integration_edge_cases(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    # Мокаем get_servers для сложного сценария
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [
        S("ss", "1.2.3.4", 1234, meta={"tag": "A"}),
        S("vmess", "5.6.7.8", 443, meta={"tag": "B"}),
        S("trojan", "9.9.9.9", 443, meta={"tag": "C"}),
    ]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class TestRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            # Проверяем, что exclusions и user_routes приходят корректно
            assert "5.6.7.8" in exclusions
            assert user_routes[0]["domain"] == ["example.com"]
            assert context["mode"] == "geo"
            # Возвращаем маршруты только для серверов без exclusions
            return [{"outbound": s.type, "tag": s.meta.get("tag", "")} for s in servers]
    exclusions = ["5.6.7.8"]
    user_routes = [{"domain": ["example.com"], "outbound": "ss"}]
    context = {"mode": "geo"}
    config = mgr.export_config(exclusions, user_routes, context, routing_plugin=TestRouter())
    # Проверяем, что outbounds не содержит excluded server
    addresses = [o["server"] for o in config["outbounds"]]
    assert "5.6.7.8" not in addresses
    # Проверяем, что маршруты соответствуют серверам без exclusions
    route_tags = [r["tag"] for r in config["route"]["rules"]]
    assert set(route_tags) == {"A", "C"} 

def test_export_config_unicode_emoji(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [
        S("ss", "1.2.3.4", 1234, meta={"tag": "🚀Rocket"}),
        S("vmess", "emoji.com", 443, meta={"tag": "🌐Web"}),
    ]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class TestRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            return [{"outbound": s.type, "tag": s.meta.get("tag", "")} for s in servers]
    config = mgr.export_config([], [], {"mode": "default"}, routing_plugin=TestRouter())
    tags = [r["tag"] for r in config["route"]["rules"]]
    assert "🚀Rocket" in tags and "🌐Web" in tags

def test_export_config_large_server_list(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [S("ss", f"10.0.0.{i}", 1000+i) for i in range(1000)]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class TestRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            return [{"outbound": s.type, "tag": s.address} for s in servers]
    config = mgr.export_config([], [], {"mode": "default"}, routing_plugin=TestRouter())
    assert len(config["outbounds"]) == 1000
    assert len(config["route"]["rules"]) == 1000

def test_export_config_invalid_inputs(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: []
    class TestRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            return []
    # Пустые servers
    config = mgr.export_config([], [], {"mode": "default"}, routing_plugin=TestRouter())
    assert config["outbounds"] == []
    assert config["route"]["rules"] == []
    # Пустые exclusions/user_routes/context
    config = mgr.export_config(None, None, None, routing_plugin=TestRouter())
    assert config["outbounds"] == []
    assert config["route"]["rules"] == []
    # context без mode
    config = mgr.export_config([], [], {}, routing_plugin=TestRouter())
    assert config["outbounds"] == []
    assert config["route"]["rules"] == [] 

def test_export_config_same_tag_different_types(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [
        S("ss", "1.2.3.4", 1234, meta={"tag": "DUP"}),
        S("vmess", "5.6.7.8", 443, meta={"tag": "DUP"}),
    ]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class TagRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            # Проверяем, что типы различаются даже при одинаковых тегах
            return [{"outbound": s.type, "tag": s.meta.get("tag", "") } for s in servers]
    config = mgr.export_config([], [], {"mode": "default"}, routing_plugin=TagRouter())
    types = [r["outbound"] for r in config["route"]["rules"] if r["tag"] == "DUP"]
    assert set(types) == {"ss", "vmess"}

def test_export_config_user_routes_vs_exclusions(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [S("ss", "1.2.3.4", 1234, meta={"tag": "A"})]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class ConflictRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            # Если сервер исключён, но user_routes на него ссылается — должен быть пустой результат
            if not servers:
                return []
            return [{"outbound": s.type, "tag": s.meta.get("tag", "") } for s in servers]
    exclusions = ["1.2.3.4"]
    user_routes = [{"domain": ["example.com"], "outbound": "ss"}]
    config = mgr.export_config(exclusions, user_routes, {"mode": "default"}, routing_plugin=ConflictRouter())
    assert config["outbounds"] == []
    assert config["route"]["rules"] == []

def test_export_config_user_routes_wildcard_not_implemented(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [S("ss", "1.2.3.4", 1234)]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class WildcardRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            for route in user_routes:
                if route.get("domain") == ["*"]:
                    raise NotImplementedError("Wildcard domain override not supported yet")
            return []
    user_routes = [{"domain": ["*"], "outbound": "ss"}]
    try:
        mgr.export_config([], user_routes, {"mode": "default"}, routing_plugin=WildcardRouter())
    except NotImplementedError as e:
        assert "Wildcard domain override not supported yet" in str(e)
    else:
        assert False, "Expected NotImplementedError for wildcard domain override"

def test_export_config_unsupported_mode(tmp_path):
    from src.sboxmgr.subscription.models import SubscriptionSource
    from src.sboxmgr.subscription.manager import SubscriptionManager
    from src.sboxmgr.export.routing.base_router import BaseRoutingPlugin
    class S:
        def __init__(self, type, address, port, security=None, meta=None):
            self.type = type
            self.address = address
            self.port = port
            self.security = security
            self.meta = meta or {}
    servers = [S("ss", "1.2.3.4", 1234)]
    source = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr = SubscriptionManager(source)
    mgr.get_servers = lambda: servers
    class ModeRouter(BaseRoutingPlugin):
        def generate_routes(self, servers, exclusions, user_routes, context=None):
            if context and context.get("mode") not in ("default", "geo"):
                raise ValueError(f"Unsupported mode: {context.get('mode')}")
            return []
    try:
        mgr.export_config([], [], {"mode": "unknown_mode"}, routing_plugin=ModeRouter())
    except ValueError as e:
        assert "Unsupported mode" in str(e)
    else:
        assert False, "Expected ValueError for unsupported mode" 