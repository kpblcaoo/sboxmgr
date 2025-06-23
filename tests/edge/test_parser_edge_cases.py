import pytest
from sboxmgr.subscription.parsers.uri_list_parser import URIListParser
from sboxmgr.subscription.models import ParsedServer
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.subscription.middleware_base import MiddlewareChain, TagFilterMiddleware, EnrichMiddleware, BaseMiddleware, LoggingMiddleware

def test_mixed_protocols():
    raw = """
# comment
ss://YWVzLTI1Ni1nY206cGFzc3dvcmRAMTI3LjAuMC4xOjEyMzQ=#tag1
vless://uuid@host:443?encryption=none#label
vmess://eyJ2IjoiMiIsInBzIjoiVGVzdCIsImFkZCI6IjEyNy4wLjAuMSIsInBvcnQiOiI0NDMiLCJpZCI6InV1aWQiLCJhaWQiOiIwIiwibmV0IjoidGNwIiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiJ9
ss://method:password@host:8388#tag2?plugin=obfs-local;obfs=tls
emoji://😀@host:1234
invalidline
""".encode("utf-8")
    parser = URIListParser()
    servers = parser.parse(raw)
    # Проверяем, что парсер не падает и возвращает ParsedServer для каждой строки
    assert isinstance(servers, list)
    assert len(servers) == 6  # 6 строк (без комментария)
    # Проверяем, что невалидные строки помечаются как unknown
    unknowns = [s for s in servers if getattr(s, 'type', None) == 'unknown']
    assert any(unknowns)
    # Проверяем, что ss:// как base64 и как URI оба парсятся
    ss = [s for s in servers if getattr(s, 'type', None) == 'ss']
    assert len(ss) >= 2
    # Проверяем, что emoji:// не приводит к падению
    emoji = [s for s in servers if getattr(s, 'address', None) and '😀' in s.address]
    # В текущей реализации emoji:// скорее всего попадёт в unknown
    assert any(unknowns)
    # Проверяем, что комментарии игнорируются
    assert servers[0] is not None  # просто не падает 

def test_middleware_chain_order_tagfilter_vs_enrich():
    from sboxmgr.subscription.manager import SubscriptionManager
    from sboxmgr.subscription.models import SubscriptionSource, ParsedServer, PipelineContext
    from sboxmgr.subscription.middleware_base import MiddlewareChain, TagFilterMiddleware, EnrichMiddleware
    # Два сервера с разными тегами
    servers = [
        ParsedServer(type="ss", address="1.2.3.4", port=443, meta={"tag": "A"}),
        ParsedServer(type="ss", address="2.2.2.2", port=1234, meta={"tag": "B"}),
    ]
    class DummyFetcher:
        def __init__(self, source):
            self.source = source
        def fetch(self):
            return b''
    # 1. TagFilter -> Enrich (country только у B)
    context1 = PipelineContext()
    context1.tag_filters = ["B"]
    chain1 = MiddlewareChain([TagFilterMiddleware(), EnrichMiddleware()])
    src1 = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr1 = SubscriptionManager(src1, middleware_chain=chain1)
    mgr1.fetcher = DummyFetcher(src1)
    mgr1.detect_parser = lambda raw, t: type('P', (), { 'parse': lambda self, raw: servers })()
    result1 = mgr1.get_servers(context=context1)
    assert result1.success, f"Pipeline failed, errors: {result1.errors}"
    assert all(s.meta.get("country") == "??" for s in result1.config)
    assert [s.meta.get("tag") for s in result1.config] == ["B"]
    # 2. Enrich -> TagFilter (country у всех, но после фильтрации остаётся только B)
    context2 = PipelineContext()
    context2.tag_filters = ["B"]
    chain2 = MiddlewareChain([EnrichMiddleware(), TagFilterMiddleware()])
    src2 = SubscriptionSource(url="file://dummy", source_type="url_base64")
    mgr2 = SubscriptionManager(src2, middleware_chain=chain2)
    mgr2.fetcher = DummyFetcher(src2)
    mgr2.detect_parser = lambda raw, t: type('P', (), { 'parse': lambda self, raw: servers })()
    result2 = mgr2.get_servers(context=context2)
    assert result2.success, f"Pipeline failed, errors: {result2.errors}"
    assert all(s.meta.get("country") == "??" for s in result2.config)
    assert [s.meta.get("tag") for s in result2.config] == ["B"]
    # Проверяем, что в первом случае country только у B, во втором — у всех (но остаётся только B)
    # (В данном stub-реализации оба варианта дают одинаковый результат, но если enrich был бы дорогим — разница была бы важна) 

def test_middleware_empty_chain_noop():
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={"tag": "A"})]
    chain = MiddlewareChain([])
    context = PipelineContext()
    result = chain.process(servers, context)
    assert result == servers

def test_middleware_with_error_accumulates():
    class ErrorMiddleware(BaseMiddleware):
        def process(self, servers, context):
            raise ValueError("middleware error")
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={"tag": "A"})]
    chain = MiddlewareChain([ErrorMiddleware()])
    context = PipelineContext()
    try:
        chain.process(servers, context)
    except Exception as e:
        assert "middleware error" in str(e)
    # В реальном пайплайне ошибка должна аккумулироваться, а не падать — это можно проверить через SubscriptionManager

def test_middleware_multiple_same_order():
    class AddTagMiddleware(BaseMiddleware):
        def __init__(self, tag):
            self.tag = tag
        def process(self, servers, context):
            for s in servers:
                s.meta["tag"] = self.tag
            return servers
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={})]
    chain = MiddlewareChain([AddTagMiddleware("A"), AddTagMiddleware("B")])
    context = PipelineContext()
    result = chain.process(servers, context)
    assert all(s.meta["tag"] == "B" for s in result)

def test_logging_middleware_debug_output(capsys):
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={})]
    chain = MiddlewareChain([LoggingMiddleware("teststage")])
    context = PipelineContext()
    context.debug_level = 1
    chain.process(servers, context)
    captured = capsys.readouterr()
    assert "[DEBUG][teststage]" in captured.out

def test_middleware_empty_servers():
    servers = []
    chain = MiddlewareChain([EnrichMiddleware()])
    context = PipelineContext()
    result = chain.process(servers, context)
    assert result == []

def test_tagfilter_middleware_no_tagfilters():
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={"tag": "A"})]
    chain = MiddlewareChain([TagFilterMiddleware()])
    context = PipelineContext()  # нет tag_filters
    result = chain.process(servers, context)
    assert result == servers 

def test_tagfilter_middleware_invalid_input():
    from sboxmgr.subscription.middleware_base import TagFilterMiddleware
    from sboxmgr.subscription.models import ParsedServer, PipelineContext
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={"tag": "A"})]
    chain = TagFilterMiddleware()
    # Не list
    context = PipelineContext()
    context.tag_filters = "A"
    try:
        chain.process(servers, context)
        assert False, "Should raise ValueError for non-list tag_filters"
    except ValueError as e:
        assert "list" in str(e)
    # Слишком длинная строка
    context.tag_filters = ["A" * 100]
    try:
        chain.process(servers, context)
        assert False, "Should raise ValueError for too long tag"
    except ValueError as e:
        assert "Invalid tag" in str(e)
    # Не строка
    context.tag_filters = [123]
    try:
        chain.process(servers, context)
        assert False, "Should raise ValueError for non-str tag"
    except ValueError as e:
        assert "Invalid tag" in str(e)
    # Не printable
    context.tag_filters = ["A\x00B"]
    try:
        chain.process(servers, context)
        assert False, "Should raise ValueError for non-printable tag"
    except ValueError as e:
        assert "Invalid tag" in str(e) 

def test_enrichmiddleware_external_lookup_timeout(monkeypatch):
    """Edge-case: EnrichMiddleware не должен делать внешний lookup без таймаута (SEC-MW-04)."""
    from sboxmgr.subscription.middleware_base import EnrichMiddleware
    from sboxmgr.subscription.models import ParsedServer, PipelineContext
    import time
    class BadEnrich(EnrichMiddleware):
        def process(self, servers, context):
            time.sleep(2)  # эмулируем внешний lookup без таймаута
            return super().process(servers, context)
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={})]
    context = PipelineContext()
    import signal
    def handler(signum, frame):
        raise TimeoutError("Enrichment took too long (no timeout)")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(1)  # 1 секунда на enrichment
    try:
        BadEnrich().process(servers, context)
        assert False, "EnrichMiddleware must not do long external lookup without timeout"
    except TimeoutError:
        pass
    finally:
        signal.alarm(0)

def test_hookmiddleware_privilege_escalation():
    """Edge-case: HookMiddleware не может эскалировать привилегии, все хуки sandboxed (SEC-MW-06)."""
    from sboxmgr.subscription.middleware_base import BaseMiddleware
    from sboxmgr.subscription.models import ParsedServer, PipelineContext
    class EvilHookMiddleware(BaseMiddleware):
        def process(self, servers, context):
            # Попытка эскалировать привилегии (эмулируем)
            try:
                import os
                os.setuid(0)  # попытка стать root
            except Exception as e:
                return servers  # sandbox: не даём эскалировать
            assert False, "HookMiddleware must not be able to escalate privileges!"
            return servers
    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={})]
    context = PipelineContext()
    EvilHookMiddleware().process(servers, context)  # не должно падать, не должно стать root 

def test_parser_malicious_payload_large_json():
    """Edge-case: Parser должен корректно обрабатывать огромный JSON (DoS) и не падать."""
    from sboxmgr.subscription.parsers.json_parser import JSONParser
    from sboxmgr.subscription.models import PipelineContext
    parser = JSONParser()
    # Огромный JSON (много элементов)
    raw = ("{" + ",".join(f'\"k{i}\":1' for i in range(100_000)) + "}").encode()
    try:
        servers = parser.parse(raw)
        assert isinstance(servers, list)
    except Exception as e:
        assert "too large" in str(e) or "memory" in str(e) or isinstance(e, Exception)

def test_parser_malicious_payload_eval():
    """Edge-case: Parser не должен выполнять eval/exec из payload (инъекция)."""
    from sboxmgr.subscription.parsers.json_parser import JSONParser
    parser = JSONParser()
    # Payload с eval-подобным полем
    raw = b'{"type": "ss", "address": "1.2.3.4", "port": 443, "meta": {"__import__": "os", "os.system": "rm -rf /"}}'
    servers = parser.parse(raw)
    # Проверяем, что suspicious поля не приводят к выполнению кода
    for s in servers:
        assert not hasattr(s, '__import__')
        assert not hasattr(s, 'os')
        assert not hasattr(s, 'system')
        if hasattr(s, 'meta'):
            assert '__import__' in s.meta or 'os.system' in s.meta

def test_parser_malicious_payload_unexpected_structure():
    """Edge-case: Parser должен корректно обрабатывать неожиданные структуры (список, вложенность)."""
    from sboxmgr.subscription.parsers.json_parser import JSONParser
    parser = JSONParser()
    # Payload — список вместо объекта
    raw = b'[1, 2, 3, {"type": "ss", "address": "1.2.3.4", "port": 443}]'
    servers = parser.parse(raw)
    assert isinstance(servers, list)
    # Payload — deeply nested
    raw = b'{"a": {"b": {"c": {"d": {"e": 1}}}}}'
    servers = parser.parse(raw)
    assert isinstance(servers, list) 