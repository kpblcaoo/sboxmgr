from sboxmgr.subscription.base_selector import DefaultSelector
from sboxmgr.subscription.models import ParsedServer


def test_empty_servers():
    selector = DefaultSelector()
    result = selector.select([])
    assert isinstance(result, list)
    assert result == []


def test_unsupported_mode():
    selector = DefaultSelector()
    servers = [ParsedServer(type="vmess", address="1.2.3.4", port=443)]
    # DefaultSelector не выбрасывает ошибку на unsupported mode, просто игнорирует
    result = selector.select(servers, mode="unsupported")
    assert isinstance(result, list)
    assert len(result) == 1


def test_wildcard_and_exclusions():
    selector = DefaultSelector()
    servers = [
        ParsedServer(type="vmess", address="1.2.3.4", port=443, meta={"tag": "A"}),
        ParsedServer(type="vmess", address="2.2.2.2", port=443, meta={"tag": "B"}),
    ]
    # user_routes = ["*"] (все), exclusions = ["A"] (исключить A)
    result = selector.select(servers, user_routes=["*"], exclusions=["A"])
    tags = [s.meta.get("tag") for s in result]
    assert "A" not in tags
    assert "B" in tags


def test_intersecting_user_routes_exclusions():
    selector = DefaultSelector()
    servers = [
        ParsedServer(type="vmess", address="1.2.3.4", port=443, meta={"tag": "A"}),
        ParsedServer(type="vmess", address="2.2.2.2", port=443, meta={"tag": "B"}),
    ]
    # user_routes = ["A"], exclusions = ["A"] (пересечение)
    result = selector.select(servers, user_routes=["A"], exclusions=["A"])
    tags = [s.meta.get("tag") for s in result]
    assert "A" not in tags
    assert "B" not in tags


def test_custom_selector_in_subscription_manager(monkeypatch):
    from sboxmgr.subscription.base_selector import BaseSelector
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import ParsedServer, SubscriptionSource

    # Мокаем HTTP запросы
    class MockResponse:
        def __init__(self, content):
            self.content = content
            class MockRaw:
                def __init__(self, content):
                    self.content = content
                def read(self, n=None):
                    return self.content
            self.raw = MockRaw(content)

        def raise_for_status(self):
            pass

    def mock_get(url, **kwargs):
        return MockResponse(b"ZGF0YQ==")  # valid base64 for "data"

    monkeypatch.setattr("requests.get", mock_get)

    class OnlyTagBSelector(BaseSelector):
        def select(self, servers, user_routes=None, exclusions=None, mode=None):
            # Фильтруем по user_routes (если указаны)
            if user_routes:
                return [s for s in servers if getattr(s, "meta", {}).get("tag") in user_routes]
            # Иначе возвращаем все серверы
            return servers

    # Подготовим SubscriptionManager с кастомным selector
    source = SubscriptionSource(
        url="http://dummy_selector_test", source_type="url_base64"
    )  # уникальный URL
    mgr = SubscriptionManager(source)
    mgr.selector = OnlyTagBSelector()
    # Очищаем кеш
    # Мокаем fetcher и parser
    class DummyFetcher:
        def __init__(self, source):
            self.source = source

        def fetch(self):
            return b"test_selector_data"

    mgr.fetcher = DummyFetcher(source)
    from sboxmgr.subscription.manager.core import DataProcessor
    mgr.data_processor = DataProcessor(mgr.fetcher, mgr.error_handler)
    mgr.data_processor.parse_servers = lambda raw, context: ([
        ParsedServer(
            type="ss",
            address="1.2.3.4",
            port=443,
            meta={
                "tag": "A",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="ss",
            address="2.2.2.2",
            port=1234,
            meta={
                "tag": "B",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="ss",
            address="3.3.3.3",
            port=1080,
            meta={
                "tag": "C",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
    ], True)
    from sboxmgr.subscription.models import PipelineContext
    context = PipelineContext(skip_policies=True)
    result = mgr.get_servers(
        user_routes=["B"],  # только серверы с тегом B
        exclusions=[],  # без исключений
        context=context,
        force_reload=True
    )  # принудительно обновляем кеш
    tags = [s.meta.get("tag") for s in result.config]
    assert tags == ["B"]
