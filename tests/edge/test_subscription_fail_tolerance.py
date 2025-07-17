import pytest

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import ParsedServer, SubscriptionSource


class DummyFetcher:
    def __init__(self, source):
        self.source = source

    def fetch(self):
        if "fail_404" in self.source.url:
            raise Exception("404 Not Found")
        if "fail_badformat" in self.source.url:
            return b"not a valid config"
        if "fail_empty" in self.source.url:
            return b""
        if "fail_crash" in self.source.url:
            raise RuntimeError("Parser crashed")
        # valid JSON config with one server
        return b'{"outbounds": [{"type": "vmess", "tag": "ok", "server_port": 443}]}'


class DummyParser:
    def parse(self, raw):
        if raw == b"not a valid config":
            raise ValueError("Parse error")
        if raw == b"":
            return []
        return [ParsedServer(type="vmess", address="ok", port=443, meta={"tag": "ok"})]


@pytest.fixture
def patch_registry(monkeypatch):
    # Гарантированно патчим detect_parser через sys.modules
    import src.sboxmgr.subscription.manager as manager_mod

    manager_mod.detect_parser = lambda raw, t: DummyParser()


def test_fail_tolerant_pipeline(monkeypatch):
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

    sources = [
        SubscriptionSource(url="http://fail_404", source_type="url_base64"),
        SubscriptionSource(url="http://fail_badformat", source_type="url_base64"),
        SubscriptionSource(url="http://fail_empty", source_type="url_base64"),
        SubscriptionSource(url="http://ok_good", source_type="url_base64"),
        SubscriptionSource(url="http://fail_crash", source_type="url_base64"),
    ]
    results = []
    for src in sources:
        try:
            mgr = SubscriptionManager(src, detect_parser=lambda raw, t: DummyParser())
            mgr.fetcher = DummyFetcher(src)
            from sboxmgr.subscription.manager.core import DataProcessor
            mgr.data_processor = DataProcessor(mgr.fetcher, mgr.error_handler)
            mgr.data_processor.parse_servers = lambda raw, context: (DummyParser().parse(raw), True)
            servers = mgr.get_servers()
            print(
                f"SRC: {src.url} | success: {getattr(servers, 'success', None)} | config: {getattr(servers, 'config', None)} | errors: {getattr(servers, 'errors', None)}"
            )
            if hasattr(servers, "success") and servers.success is False:
                results.append((src.url, "fail", servers))
            else:
                results.append((src.url, "ok", servers))
        except Exception as e:
            print(f"SRC: {src.url} | EXC: {e}")
            results.append((src.url, "fail", str(e)))
    oks = [r for r in results if r[1] == "ok"]
    assert any(oks), "Должна быть хотя бы одна успешная подписка"
    assert len(results) == 5
    for url, status, _ in results:
        if url.startswith("file://fail_") and url != "file://fail_empty":
            assert status == "fail"
        if url == "file://ok_good":
            assert status == "ok"
