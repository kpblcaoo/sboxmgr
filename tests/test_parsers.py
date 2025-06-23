import pytest
from sboxmgr.subscription.parsers.base64_parser import Base64Parser
from sboxmgr.subscription.parsers.json_parser import JSONParser
from sboxmgr.subscription.parsers.uri_list_parser import URIListParser

SS_BASE64 = "YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4"  # pragma: allowlist secret
SS_URI = "ss://aes-256-gcm:pass@example.com:8388#ssuri"  # pragma: allowlist secret
VMESS_JSON = '{"type": "vmess", "address": "vm.com", "port": 443}'  # pragma: allowlist secret
MIXED_LIST = """
# comment
ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#emoji🚀?plugin=obfs  # pragma: allowlist secret
vmess://eyJhZGQiOiJ2bS5jb20iLCJwb3J0Ijo0NDN9  # pragma: allowlist secret
ss://aes-256-gcm:pass@example.com:8388#ssuri  # pragma: allowlist secret
"""
INVALID = "not a valid subscription"

@pytest.mark.parametrize("parser_cls, raw, should_fail, expect_ss", [
    (Base64Parser, SS_BASE64.encode(), False, True),
    (URIListParser, SS_URI.encode(), False, True),
    (JSONParser, VMESS_JSON.encode(), False, False),
    (URIListParser, MIXED_LIST.encode(), False, True),
    (Base64Parser, INVALID.encode(), True, False),
])
def test_parsers_edge_cases(parser_cls, raw, should_fail, expect_ss):
    parser = parser_cls()
    if should_fail:
        with pytest.raises(Exception):
            parser.parse(raw)
    else:
        servers = parser.parse(raw)
        if expect_ss:
            assert any(s.type == "ss" for s in servers)
        # Проверяем emoji/tag только если реально есть в тестовых данных
        # (например, в MIXED_LIST, но не в SS_URI)
        # if parser_cls is URIListParser and ...: # можно добавить отдельный тест для emoji 

def test_uri_list_parser_edge_cases():
    from sboxmgr.subscription.parsers.uri_list_parser import URIListParser
    parser = URIListParser()
    with open('src/sboxmgr/examples/example_uri_list.txt', 'rb') as f:
        raw = f.read()
    servers = parser.parse(raw)
    # Проверяем, что все ожидаемые типы присутствуют
    types = {s.type for s in servers}
    assert 'ss' in types
    assert 'vless' in types
    assert 'vmess' in types
    assert 'trojan' in types
    # Проверяем, что хотя бы один тег содержит emoji или unicode
    assert any('emoji' in (s.meta or {}).get('tag', '').lower() or '🚀' in (s.meta or {}).get('tag', '') for s in servers)
    # Проверяем, что парсер не падает на пустых строках, комментариях, невалидных строках
    # (если не выброшено исключение — тест пройден) 