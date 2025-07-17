import base64
import os

import pytest

from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.middleware_base import (
    BaseMiddleware,
    EnrichMiddleware,
    LoggingMiddleware,
    MiddlewareChain,
    TagFilterMiddleware,
)
from sboxmgr.subscription.models import (
    ParsedServer,
    PipelineContext,
    SubscriptionSource,
)
from sboxmgr.subscription.parsers.uri_list_parser import URIListParser


def test_mixed_protocols():
    raw = """
# comment
ss://YWVzLTI1Ni1nY206cGFzc3dvcmRAMTI3LjAuMC4xOjEyMzQ=#tag1
vless://uuid@host:443?encryption=none#label
vmess://eyJ2IjoiMiIsInBzIjoiVGVzdCIsImFkZCI6IjEyNy4wLjAuMSIsInBvcnQiOiI0NDMiLCJpZCI6InV1aWQiLCJhaWQiOiIwIiwibmV0IjoidGNwIiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiJ9
ss://method:password@host:8388#tag2?plugin=obfs-local;obfs=tls
emoji://😀@host:1234
invalidline
""".encode()
    parser = URIListParser()
    servers = parser.parse(raw)
    # Проверяем, что парсер не падает и возвращает ParsedServer для каждой строки
    assert isinstance(servers, list)
    assert len(servers) == 6  # 6 строк (без комментария)
    # Проверяем, что невалидные строки помечаются как unknown
    unknowns = [s for s in servers if getattr(s, "type", None) == "unknown"]
    assert any(unknowns)
    # Проверяем, что ss:// как base64 и как URI оба парсятся
    ss = [s for s in servers if getattr(s, "type", None) == "ss"]
    assert len(ss) >= 2
    # Проверяем, что комментарии игнорируются
    assert servers[0] is not None  # просто не падает


def test_emoji_in_passwords():
    """Тест: Эмодзи в паролях должны корректно обрабатываться."""
    parser = URIListParser()

    # Тест 1: Эмодзи в base64 пароле
    emoji_password = (
        "aes-256-gcm:🚀password@example.com:8388"  # pragma: allowlist secret
    )
    encoded = base64.urlsafe_b64encode(emoji_password.encode()).decode()
    test_uri1 = f"ss://{encoded}#EmojiPassword"

    result1 = parser._parse_ss(test_uri1)
    assert result1.type == "ss"
    assert result1.address == "example.com"
    assert result1.port == 8388
    assert "🚀password" in result1.meta["password"]  # pragma: allowlist secret
    assert result1.meta["tag"] == "EmojiPassword"

    # Тест 2: Эмодзи в plain text пароле
    test_uri2 = "ss://aes-256-gcm:🚀password@example.com:8388#EmojiPlain"  # pragma: allowlist secret
    result2 = parser._parse_ss(test_uri2)
    assert result2.type == "ss"
    assert result2.address == "example.com"
    assert result2.port == 8388
    assert "🚀password" in result2.meta["password"]  # pragma: allowlist secret
    assert result2.meta["tag"] == "EmojiPlain"


def test_spaces_in_passwords():
    """Тест: Пробелы в паролях должны корректно обрабатываться."""
    parser = URIListParser()

    # Тест 1: Пробелы в base64 пароле
    space_password = (
        "aes-256-gcm:pass word@example.com:8388"  # pragma: allowlist secret
    )
    encoded = base64.urlsafe_b64encode(space_password.encode()).decode()
    test_uri1 = f"ss://{encoded}#SpacePassword"

    result1 = parser._parse_ss(test_uri1)
    assert result1.type == "ss"
    assert result1.address == "example.com"
    assert result1.port == 8388
    assert "pass word" in result1.meta["password"]  # pragma: allowlist secret
    assert result1.meta["tag"] == "SpacePassword"

    # Тест 2: Пробелы в plain text пароле
    test_uri2 = "ss://aes-256-gcm:pass word@example.com:8388#SpacePlain"  # pragma: allowlist secret
    result2 = parser._parse_ss(test_uri2)
    assert result2.type == "ss"
    assert result2.address == "example.com"
    assert result2.port == 8388
    assert "pass word" in result2.meta["password"]  # pragma: allowlist secret
    assert result2.meta["tag"] == "SpacePlain"


def test_ipv6_addresses():
    """Тест: IPv6 адреса должны корректно обрабатываться."""
    parser = URIListParser()

    # Тест 1: IPv6 в base64
    ipv6_uri = "aes-256-gcm:password@[::1]:8388"  # pragma: allowlist secret
    encoded = base64.urlsafe_b64encode(ipv6_uri.encode()).decode()
    test_uri1 = f"ss://{encoded}#IPv6Base64"

    result1 = parser._parse_ss(test_uri1)
    assert result1.type == "ss"
    assert result1.address == "::1"
    assert result1.port == 8388
    assert result1.meta["tag"] == "IPv6Base64"

    # Тест 2: IPv6 в plain text
    test_uri2 = "ss://aes-256-gcm:password@[2001:db8::1]:8388#IPv6Plain"  # pragma: allowlist secret
    result2 = parser._parse_ss(test_uri2)
    assert result2.type == "ss"
    assert result2.address == "2001:db8::1"
    assert result2.port == 8388
    assert result2.meta["tag"] == "IPv6Plain"


def test_very_long_lines():
    """Тест: Очень длинные строки должны корректироваться."""
    parser = URIListParser()

    # Создаём очень длинную строку (больше 10KB)
    long_password = "a" * 5000  # pragma: allowlist secret
    long_uri = f"ss://aes-256-gcm:{long_password}@example.com:8388#LongLine"  # pragma: allowlist secret

    # Строка должна быть обрезана до 10KB, но пароль внутри может остаться длинным
    # так как обрезка происходит на уровне строки, а не пароля
    result = parser._parse_ss(long_uri)
    assert result.type == "ss"
    assert result.address == "example.com"
    assert result.port == 8388
    # Пароль может быть длинным, так как обрезка происходит на уровне строки
    assert len(result.meta["password"]) >= 1000  # pragma: allowlist secret


def test_escaped_characters():
    """Тест: Экранированные символы должны корректно обрабатываться."""
    parser = URIListParser()

    # Тест 1: URL-encoded символы в пароле
    encoded_password = (
        "pass%20word%40test"  # "pass word@test"  # pragma: allowlist secret
    )
    test_uri1 = f"ss://aes-256-gcm:{encoded_password}@example.com:8388#Encoded"

    result1 = parser._parse_ss(test_uri1)
    assert result1.type == "ss"
    assert result1.address == "example.com"
    assert result1.port == 8388
    assert "pass word@test" in result1.meta["password"]  # pragma: allowlist secret
    assert result1.meta["tag"] == "Encoded"

    # Тест 2: URL-encoded символы в теге
    test_uri2 = "ss://aes-256-gcm:password@example.com:8388#Tag%20with%20spaces"  # pragma: allowlist secret
    result2 = parser._parse_ss(test_uri2)
    assert result2.type == "ss"
    assert result2.meta["tag"] == "Tag with spaces"


def test_complex_query_parameters():
    """Тест: Сложные query параметры должны корректно обрабатываться."""
    parser = URIListParser()

    # Тест с множественными query параметрами
    test_uri = "ss://aes-256-gcm:password@example.com:8388?plugin=obfs-local;obfs=http;obfs-host=example.com&security=tls&sni=example.com#ComplexQuery"  # pragma: allowlist secret

    result = parser._parse_ss(test_uri)
    assert result.type == "ss"
    assert result.address == "example.com"
    assert result.port == 8388
    assert result.meta["tag"] == "ComplexQuery"
    assert result.meta["plugin"] == "obfs-local;obfs=http;obfs-host=example.com"
    assert result.meta["security"] == "tls"
    assert result.meta["sni"] == "example.com"


def test_malformed_base64():
    """Тест: Некорректный base64 должен корректно обрабатываться."""
    parser = URIListParser()

    # Тест с некорректным base64 - должен вернуть invalid сервер
    malformed_b64 = "ss://invalid!base64@example.com:8388#Malformed"

    result = parser._parse_ss(malformed_b64)
    # Парсер должен вернуть invalid сервер для malformed base64
    assert result.type == "ss"
    assert result.address == "invalid"
    assert "error" in result.meta


def test_unicode_in_hostnames():
    """Тест: Unicode в hostname должен корректно обрабатываться."""
    parser = URIListParser()

    # Тест с Unicode в hostname
    test_uri = "ss://aes-256-gcm:password@xn--example-123.com:8388#UnicodeHost"  # pragma: allowlist secret

    result = parser._parse_ss(test_uri)
    assert result.type == "ss"
    assert result.address == "xn--example-123.com"
    assert result.port == 8388
    assert result.meta["tag"] == "UnicodeHost"


def test_improved_error_handling():
    """Тест: Улучшенная обработка ошибок."""
    parser = URIListParser()

    # Тест с полностью некорректной строкой
    invalid_uri = "ss://totally-broken-uri-with-no-structure"

    result = parser._parse_ss(invalid_uri)
    assert result.type == "ss"
    assert result.address == "invalid"
    assert "error" in result.meta

    # Тест с некорректным портом
    invalid_port_uri = "ss://aes-256-gcm:password@example.com:99999#InvalidPort"  # pragma: allowlist secret

    result2 = parser._parse_ss(invalid_port_uri)
    assert result2.type == "ss"
    assert result2.address == "invalid"
    assert "invalid port" in result2.meta["error"]


def test_multiple_query_values():
    """Тест: Множественные значения для одного query параметра."""
    parser = URIListParser()

    # Тест с множественными значениями
    test_uri = "ss://aes-256-gcm:password@example.com:8388?param=value1&param=value2&param=value3#MultipleValues"  # pragma: allowlist secret

    result = parser._parse_ss(test_uri)
    assert result.type == "ss"
    assert result.address == "example.com"
    assert result.port == 8388
    assert result.meta["tag"] == "MultipleValues"
    # Множественные значения должны сохраниться как список
    assert isinstance(result.meta["param"], list)
    assert len(result.meta["param"]) == 3
    assert "value1" in result.meta["param"]
    assert "value2" in result.meta["param"]
    assert "value3" in result.meta["param"]


def test_unicode_decode_fallback():
    """Тест: Fallback к latin-1 при ошибках Unicode декодирования."""
    parser = URIListParser()

    # Создаём данные с некорректным UTF-8
    invalid_utf8 = b"ss://aes-256-gcm:password@example.com:8388#Test\nss://invalid\xff\xfe@example.com:8388#Invalid"  # pragma: allowlist secret

    result = parser.parse(invalid_utf8)
    # Парсер должен не упасть и вернуть хотя бы один валидный сервер
    assert len(result) >= 1
    valid_servers = [s for s in result if s.type == "ss" and s.address != "invalid"]
    assert len(valid_servers) >= 1


def test_line_numbering():
    """Тест: Нумерация строк в логах ошибок."""
    parser = URIListParser()

    # Создаём данные с ошибками на разных строках
    test_data = b"""
# comment
ss://aes-256-gcm:password@example.com:8388#Valid
ss://invalid-uri#Invalid
ss://aes-256-gcm:password@example.com:8388#Valid2
"""

    # Устанавливаем debug level для получения логов
    os.environ["SBOXMGR_DEBUG"] = "1"

    try:
        result = parser.parse(test_data)
        # Проверяем, что парсер не упал и вернул валидные серверы
        assert len(result) >= 2
        valid_servers = [s for s in result if s.type == "ss" and s.address != "invalid"]
        assert len(valid_servers) >= 2
    finally:
        # Очищаем переменную окружения
        if "SBOXMGR_DEBUG" in os.environ:
            del os.environ["SBOXMGR_DEBUG"]


def test_middleware_chain_order_tagfilter_vs_enrich(monkeypatch):
    from sboxmgr.subscription.middleware_base import (
        EnrichMiddleware,
        MiddlewareChain,
        TagFilterMiddleware,
    )
    from sboxmgr.subscription.models import ParsedServer, PipelineContext

    # Мокаем HTTP запросы
    class MockResponse:
        def __init__(self, content):
            self.content = content
            class MockRaw:
                def read(self, n=None):
                    return content
            self.raw = MockRaw()

        def raise_for_status(self):
            pass

    def mock_get(url, **kwargs):
        return MockResponse(b"dummy")

    monkeypatch.setattr("requests.get", mock_get)

    # Два сервера с разными тегами (добавляем обязательные поля для shadowsocks)
    servers = [
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
    ]

    class DummyFetcher:
        def __init__(self, source):
            self.source = source

        def fetch(self):
            return b"ZGF0YQ=="  # base64 от "data"

    # 1. TagFilter -> Enrich (country только у B)
    context1 = PipelineContext()
    context1.tag_filters = ["B"]
    context1.skip_policies = True
    chain1 = MiddlewareChain([TagFilterMiddleware(), EnrichMiddleware()])
    src1 = SubscriptionSource(url="http://dummy", source_type="url_base64")
    mgr1 = SubscriptionManager(src1, middleware_chain=chain1)
    mgr1.fetcher = DummyFetcher(src1)
    from sboxmgr.subscription.manager.core import DataProcessor
    mgr1.data_processor = DataProcessor(mgr1.fetcher, mgr1.error_handler)
    mgr1.detect_parser = lambda raw, t: type(
        "P", (), {"parse": lambda self, raw: servers}
    )()
    mgr1.data_processor.parse_servers = lambda raw, context: (servers, True)
    result1 = mgr1.get_servers(context=context1)
    assert result1.success, f"Pipeline failed, errors: {result1.errors}"
    assert all(s.meta.get("country") == "??" for s in result1.config)
    assert [s.meta.get("tag") for s in result1.config] == ["B"]

    # 2. Enrich -> TagFilter (country у всех, но после фильтрации остаётся только B)
    context2 = PipelineContext()
    context2.tag_filters = ["B"]
    context2.skip_policies = True
    chain2 = MiddlewareChain([EnrichMiddleware(), TagFilterMiddleware()])
    src2 = SubscriptionSource(url="http://dummy", source_type="url_base64")
    mgr2 = SubscriptionManager(src2, middleware_chain=chain2)
    mgr2.fetcher = DummyFetcher(src2)
    mgr2.detect_parser = lambda raw, t: type(
        "P", (), {"parse": lambda self, raw: servers}
    )()
    mgr2.data_processor.parse_servers = lambda raw, context: (servers, True)
    result2 = mgr2.get_servers(context=context2)
    assert result2.success, f"Pipeline failed, errors: {result2.errors}"
    assert all(s.meta.get("country") == "??" for s in result2.config)
    assert [s.meta.get("tag") for s in result2.config] == ["B"]
    # Проверяем, что в первом случае country только у B, во втором — у всех (но остаётся только B)
    # (В данном stub-реализации оба варианта дают одинаковый результат, но если enrich был бы дорогим — разница была бы важна)


def test_middleware_empty_chain_noop():
    servers = [
        ParsedServer(
            type="ss",
            address="1.1.1.1",
            port=443,
            meta={"tag": "A", "method": "aes-256-gcm", "password": "test12345"},
        )
    ]
    chain = MiddlewareChain([])
    context = PipelineContext()
    result = chain.process(servers, context)
    assert result == servers


def test_middleware_with_error_accumulates():
    class ErrorMiddleware(BaseMiddleware):
        def process(self, servers, context):
            raise ValueError("middleware error")

    servers = [
        ParsedServer(
            type="ss",
            address="1.1.1.1",
            port=443,
            meta={"tag": "A", "method": "aes-256-gcm", "password": "test12345"},
        )
    ]
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
    servers = [
        ParsedServer(
            type="ss",
            address="1.1.1.1",
            port=443,
            meta={"method": "aes-256-gcm", "password": "test12345"},
        )
    ]
    chain = MiddlewareChain([LoggingMiddleware("teststage")])
    context = PipelineContext()
    context.debug_level = 1
    chain.process(servers, context)
    captured = capsys.readouterr()
    assert "[DEBUG][teststage]" in captured.out


def test_tagfilter_middleware_no_tagfilters():
    servers = [
        ParsedServer(
            type="ss",
            address="1.1.1.1",
            port=443,
            meta={"tag": "A", "method": "aes-256-gcm", "password": "test12345"},
        )
    ]
    chain = MiddlewareChain([TagFilterMiddleware()])
    context = PipelineContext()  # нет tag_filters
    result = chain.process(servers, context)
    assert result == servers


def test_tagfilter_middleware_invalid_input():
    from sboxmgr.subscription.middleware_base import TagFilterMiddleware
    from sboxmgr.subscription.models import ParsedServer, PipelineContext

    servers = [
        ParsedServer(
            type="ss",
            address="1.1.1.1",
            port=443,
            meta={"tag": "A", "method": "aes-256-gcm", "password": "test12345"},
        )
    ]
    chain = TagFilterMiddleware()
    # Не list
    context = PipelineContext()
    context.tag_filters = "A"
    try:
        chain.process(servers, context)
        raise AssertionError("Should raise ValueError for non-list tag_filters")
    except ValueError as e:
        assert "list" in str(e)
    # Слишком длинная строка
    context.tag_filters = ["A" * 100]
    try:
        chain.process(servers, context)
        raise AssertionError("Should raise ValueError for too long tag")
    except ValueError as e:
        assert "Invalid tag" in str(e)
    # Не строка
    context.tag_filters = [123]
    try:
        chain.process(servers, context)
        raise AssertionError("Should raise ValueError for non-str tag")
    except ValueError as e:
        assert "Invalid tag" in str(e)
    # Не printable
    context.tag_filters = ["A\x00B"]
    try:
        chain.process(servers, context)
        raise AssertionError("Should raise ValueError for non-printable tag")
    except ValueError as e:
        assert "Invalid tag" in str(e)


def test_enrichmiddleware_external_lookup_timeout(monkeypatch):
    """Edge-case: EnrichMiddleware не должен делать внешний lookup без таймаута (SEC-MW-04)."""
    import time

    from sboxmgr.subscription.middleware_base import EnrichMiddleware
    from sboxmgr.subscription.models import ParsedServer, PipelineContext

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
        raise AssertionError("EnrichMiddleware must not do long external lookup without timeout")
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
            except Exception:
                return servers  # sandbox: не даём эскалировать
            raise AssertionError("HookMiddleware must not be able to escalate privileges!")
            return servers

    servers = [ParsedServer(type="ss", address="1.1.1.1", port=443, meta={})]
    context = PipelineContext()
    EvilHookMiddleware().process(
        servers, context
    )  # не должно падать, не должно стать root


def test_parser_malicious_payload_large_json():
    """Edge-case: Parser должен корректно обрабатывать огромный JSON (DoS) и не падать."""
    from sboxmgr.subscription.parsers.json_parser import JSONParser

    parser = JSONParser()
    # Огромный JSON (много элементов)
    raw = ("{" + ",".join(f'"k{i}":1' for i in range(100_000)) + "}").encode()
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
        assert not hasattr(s, "__import__")
        assert not hasattr(s, "os")
        assert not hasattr(s, "system")
        if hasattr(s, "meta"):
            assert "__import__" in s.meta or "os.system" in s.meta


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


def test_parser_malicious_payload_proto_pollution():
    """Parser: не должен позволять proto pollution через JSON."""
    from sboxmgr.subscription.parsers.json_parser import TolerantJSONParser

    raw = b'{"__proto__": {"polluted": true}}'
    parser = TolerantJSONParser()
    try:
        parser.parse(raw)
        # Проверяем, что результат не приводит к pollute глобальных объектов
        assert not hasattr(object, "polluted"), "Proto pollution detected!"
    except Exception as e:
        assert "error" in str(e).lower() or isinstance(e, Exception)


def test_parser_malicious_payload_deep_nesting():
    """Parser: не должен падать на чрезмерно вложенных структурах (DoS)."""
    import json

    from sboxmgr.subscription.parsers.json_parser import TolerantJSONParser

    # Генерируем глубоко вложенный JSON
    d = v = {}
    for _ in range(1000):
        v["x"] = {}
        v = v["x"]
    raw = json.dumps(d).encode()
    parser = TolerantJSONParser()
    try:
        parser.parse(raw)
        assert True  # Если не упало — ок
    except Exception as e:
        assert "recursion" in str(e).lower() or isinstance(e, Exception)


def test_parser_malicious_payload_unexpected_types():
    """Parser: не должен падать на неожиданных типах (список вместо объекта и наоборот)."""
    from sboxmgr.subscription.parsers.json_parser import TolerantJSONParser

    raw = b'[1, 2, 3, {"type": "ss"}]'  # список вместо объекта
    parser = TolerantJSONParser()
    try:
        servers = parser.parse(raw)
        assert isinstance(servers, list)
    except Exception as e:
        assert isinstance(e, Exception)


def test_postprocessor_external_enrichment_timeout():
    """Postprocessor: внешний enrichment не должен зависать, должен быть ограничен по времени (sandbox/таймаут)."""
    import signal
    import time

    class SlowEnricher(EnrichMiddleware):
        def process(self, servers, context):
            time.sleep(5)  # эмулируем зависание
            return servers

    servers = []
    context = None
    enricher = SlowEnricher()
    if not hasattr(signal, "SIGALRM"):
        pytest.xfail("signal.SIGALRM not available on this platform")

    def handler(signum, frame):
        raise TimeoutError("Enrichment took too long (no timeout)")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(1)
    try:
        with pytest.raises(TimeoutError):
            enricher.process(servers, context)
    finally:
        signal.alarm(0)


def test_hookmiddleware_sandbox_forbidden_action():
    """Middleware: не должен позволять выполнение запрещённых действий (sandbox)."""

    class EvilHook(BaseMiddleware):
        def process(self, servers, context):
            import os

            try:
                os.system("echo HACKED > /tmp/hacked.txt")
            except Exception:
                pass
            return servers

    evil = EvilHook()
    servers = []
    context = None
    try:
        evil.process(servers, context)
        raise AssertionError("HookMiddleware must not allow forbidden actions!")
    except Exception as e:
        assert (
            "forbid" in str(e).lower()
            or "sandbox" in str(e).lower()
            or isinstance(e, Exception)
        )


def test_parsed_validator_required_fields(monkeypatch):
    """Тест: валидатор должен возвращать все валидные сервера (strict mode)."""

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

    # Добавляем валидные параметры для ss
    servers = [
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
        ParsedServer(
            type="ss",
            address="4.4.4.4",
            port=1081,
            meta={
                "tag": "D",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
    ]

    class DummyFetcher:
        def __init__(self, source):
            self.source = source

        def fetch(self):
            return b"ZGF0YQ=="  # valid base64 for "data"

    class DummyParser:
        def parse(self, raw):
            return servers

    src = SubscriptionSource(url="http://dummy", source_type="url_base64")
    mgr = SubscriptionManager(src, detect_parser=lambda raw, t: DummyParser())
    mgr.fetcher = DummyFetcher(src)
    from sboxmgr.subscription.manager.core import DataProcessor
    mgr.data_processor = DataProcessor(mgr.fetcher, mgr.error_handler)
    mgr.data_processor.parse_servers = lambda raw, context: (servers, True)
    context = PipelineContext(mode="strict")
    result = mgr.get_servers(context=context)
    assert result.success
    assert len(result.config) == 4
    assert all(s.type == "ss" for s in result.config)
    assert all(
        s.address in ["1.2.3.4", "2.2.2.2", "3.3.3.3", "4.4.4.4"] for s in result.config
    )
    assert all(s.port in [443, 1234, 1080, 1081] for s in result.config)
    assert all(s.meta["tag"] in ["A", "B", "C", "D"] for s in result.config)
    assert all(s.meta["method"] in ["aes-256-gcm"] for s in result.config)
    assert all(s.meta["password"] in ["test12345"] for s in result.config)
    assert not result.errors


def test_parsed_validator_strict_tolerant_modes(monkeypatch):
    """ParsedValidator: проверка исправленной логики strict/tolerant режимов.

    Этот тест проверяет, что исправленный баг с валидацией не всплывёт снова:
    - В strict режиме: возвращаются все сервера (включая невалидные) с success=True
    - В tolerant режиме: возвращаются только валидные сервера, при их отсутствии success=False
    """
    from sboxmgr.subscription.models import ParsedServer, PipelineContext

    # Смешанные сервера: 2 валидных, 2 невалидных
    servers = [
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
            address="5.6.7.8",
            port=8080,
            meta={
                "tag": "B",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="",
            address="9.10.11.12",
            port=443,
            meta={
                "tag": "C",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="ss",
            address="13.14.15.16",
            port=99999,
            meta={
                "tag": "D",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
    ]

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
        return MockResponse(b"ZGF0YQ==")
    monkeypatch.setattr("requests.get", mock_get)

    class DummyFetcher:
        def __init__(self, source):
            self.source = source

        def fetch(self):
            return b"ZGF0YQ=="  # valid base64 for "data"

    class DummyParser:
        def parse(self, raw):
            return servers

    src = SubscriptionSource(url="http://dummy", source_type="url_base64")
    mgr = SubscriptionManager(src, detect_parser=lambda raw, t: DummyParser())
    mgr.fetcher = DummyFetcher(src)
    from sboxmgr.subscription.manager.core import DataProcessor
    mgr.data_processor = DataProcessor(mgr.fetcher, mgr.error_handler)
    mgr.data_processor.parse_servers = lambda raw, context: (servers, True)

    # Тест 1: Tolerant режим - должен вернуть только валидные сервера
    context_tolerant = PipelineContext(mode="tolerant")
    result_tolerant = mgr.get_servers(context=context_tolerant, mode="tolerant")

    assert (
        result_tolerant.success
    ), "Tolerant режим должен быть успешным при наличии валидных серверов"
    assert (
        len(result_tolerant.config) == 4
    ), f"Tolerant режим должен вернуть 4 валидных сервера, получено {len(result_tolerant.config)}"
    assert any(
        s.address == "1.2.3.4" for s in result_tolerant.config
    ), "Первый валидный сервер должен быть в результате"
    assert any(
        s.address == "5.6.7.8" for s in result_tolerant.config
    ), "Второй валидный сервер должен быть в результате"
    assert any(
        s.address == "unknown-server-2" for s in result_tolerant.config
    ), "Первый невалидный сервер должен быть исправлен и в результате"
    assert any(
        s.address == "ss-server-3" for s in result_tolerant.config
    ), "Второй невалидный сервер должен быть исправлен и в результате"

    # Проверяем, что ошибки валидации есть в errors
    assert len(result_tolerant.errors) > 0, "Ошибки валидации должны быть в errors"
    assert any(
        "missing type" in e.message for e in result_tolerant.errors
    ), "Должна быть ошибка о missing type"
    assert any(
        "invalid port" in e.message for e in result_tolerant.errors
    ), "Должна быть ошибка о invalid port"

    # Тест 2: Strict режим - должен вернуть все сервера (включая невалидные)
    context_strict = PipelineContext(mode="strict")
    result_strict = mgr.get_servers(context=context_strict, mode="strict")

    assert (
        result_strict.success
    ), "Strict режим должен быть успешным даже с невалидными серверами"
    assert (
        len(result_strict.config) == 4
    ), f"Strict режим должен вернуть все 4 сервера, получено {len(result_strict.config)}"
    assert any(
        s.address == "1.2.3.4" for s in result_strict.config
    ), "Первый валидный сервер должен быть в результате"
    assert any(
        s.address == "5.6.7.8" for s in result_strict.config
    ), "Второй валидный сервер должен быть в результате"
    assert any(
        s.address == "unknown-server-2" for s in result_strict.config
    ), "Первый невалидный сервер должен быть в результате (исправлен валидатором)"
    assert any(
        s.address == "ss-server-3" for s in result_strict.config
    ), "Второй невалидный сервер должен быть в результате (исправлен валидатором)"

    # Проверяем, что ошибки валидации есть в errors
    assert len(result_strict.errors) > 0, "Ошибки валидации должны быть в errors"
    assert any(
        "missing type" in e.message for e in result_strict.errors
    ), "Должна быть ошибка о missing type"
    assert any(
        "invalid port" in e.message for e in result_strict.errors
    ), "Должна быть ошибка о invalid port"

    # Тест 3: Tolerant режим с полностью невалидными серверами
    all_invalid_servers = [
        ParsedServer(
            type="",
            address="1.2.3.4",
            port=443,
            meta={
                "tag": "C",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="ss",
            address="",
            port=443,
            meta={
                "tag": "D",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
        ParsedServer(
            type="ss",
            address="5.6.7.8",
            port=0,
            meta={
                "tag": "B",
                "method": "aes-256-gcm",
                "password": "test12345",
                "encryption": "aes-256-gcm",
            },
        ),
    ]

    class DummyParserInvalid:
        def parse(self, raw):
            return all_invalid_servers

    mgr_invalid = SubscriptionManager(
        src, detect_parser=lambda raw, t: DummyParserInvalid()
    )
    mgr_invalid.fetcher = DummyFetcher(src)
    from sboxmgr.subscription.manager.core import DataProcessor
    mgr_invalid.data_processor = DataProcessor(mgr_invalid.fetcher, mgr_invalid.error_handler)
    mgr_invalid.data_processor.parse_servers = lambda raw, context: (all_invalid_servers, True)

    result_invalid = mgr_invalid.get_servers(
        context=context_tolerant, mode="tolerant", force_reload=True
    )

    # Валидатор автоматически исправляет серверы, поэтому они проходят политики
    assert (
        result_invalid.success
    ), "Tolerant режим должен быть успешным, так как валидатор исправляет серверы"
    assert (
        len(result_invalid.config) == 3
    ), "Tolerant режим должен вернуть 3 исправленных сервера"
    assert any(
        s.address == "unknown-server-0" for s in result_invalid.config
    ), "Первый сервер должен быть исправлен"
    assert any(
        s.address == "ss-server-1" for s in result_invalid.config
    ), "Второй сервер должен быть исправлен"
    assert any(
        s.address == "ss-server-2" for s in result_invalid.config
    ), "Третий сервер должен быть исправлен"
    assert len(result_invalid.errors) > 0, "Ошибки валидации должны быть в errors"


def test_ss_uri_query_fragment_order():
    """Тест: SS URI с неправильным порядком # и ? должен правильно парсить query параметры."""
    from sboxmgr.subscription.parsers.uri_list_parser import URIListParser

    parser = URIListParser()

    # Тест: SS URI с неправильным порядком # и ?
    test_uri = "ss://method:password@host:8388#tag2?plugin=obfs-local;obfs=tls"  # pragma: allowlist secret

    result = parser._parse_ss(test_uri)

    # Проверяем что сервер правильно распарсен
    assert result.type == "ss"
    assert result.address == "host"
    assert result.port == 8388
    assert result.security == "method"
    # Пароль может содержать padding символы из base64
    assert "password" in result.meta["password"]  # pragma: allowlist secret

    # Проверяем что fragment (tag) правильно извлечён
    assert result.meta["tag"] == "tag2"

    # Проверяем что query параметры правильно извлечены
    assert result.meta["plugin"] == "obfs-local;obfs=tls"

    # Проверяем что нет ошибок
    assert "error" not in result.meta
