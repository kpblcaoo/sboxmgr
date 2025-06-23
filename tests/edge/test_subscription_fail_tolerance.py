import pytest
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
import tempfile
import os
import sys

class DummyFetcher:
    def __init__(self, source):
        self.source = source
    def fetch(self):
        if self.source.url == "fail://404":
            raise Exception("404 Not Found")
        if self.source.url == "fail://badformat":
            return b"not a valid config"
        if self.source.url == "fail://empty":
            return b""
        if self.source.url == "fail://crash":
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
    # Патчим registry для fetcher
    monkeypatch.setattr("src.sboxmgr.subscription.manager.get_plugin", lambda t: DummyFetcher)
    # Гарантированно патчим detect_parser через sys.modules
    import types
    import src.sboxmgr.subscription.manager as manager_mod
    manager_mod.detect_parser = lambda raw, t: DummyParser()


def test_fail_tolerant_pipeline(patch_registry):
    sources = [
        SubscriptionSource(url="fail://404", source_type="url_base64"),
        SubscriptionSource(url="fail://badformat", source_type="url_base64"),
        SubscriptionSource(url="fail://empty", source_type="url_base64"),
        SubscriptionSource(url="ok://good", source_type="url_base64"),
        SubscriptionSource(url="fail://crash", source_type="url_base64"),
    ]
    results = []
    for src in sources:
        try:
            mgr = SubscriptionManager(src, detect_parser=lambda raw, t: DummyParser())
            mgr.fetcher = DummyFetcher(src)
            servers = mgr.get_servers()
            if hasattr(servers, 'success') and servers.success is False:
                results.append((src.url, "fail", servers))
            else:
                results.append((src.url, "ok", servers))
        except Exception as e:
            results.append((src.url, "fail", str(e)))
    oks = [r for r in results if r[1] == "ok"]
    fails = [r for r in results if r[1] == "fail"]
    assert any(oks), "Должна быть хотя бы одна успешная подписка"
    assert len(results) == 5
    for url, status, _ in results:
        if url.startswith("fail://") and url != "fail://empty":
            assert status == "fail"
        if url == "ok://good":
            assert status == "ok" 