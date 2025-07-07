import os

from sboxmgr.subscription.parsers.uri_list_parser import URIListParser


def test_uri_list_parser():
    example_path = os.path.join(
        os.path.dirname(__file__), "../src/sboxmgr/examples/example_uri_list.txt"
    )
    with open(example_path, "rb") as f:
        raw = f.read()
    parser = URIListParser()
    servers = parser.parse(raw)
    # Проверяем, что парсятся только валидные строки (ss, vless, vmess, unknown)
    assert isinstance(servers, list)
    assert any(s.type == "ss" for s in servers)
    assert any(s.type == "vless" for s in servers)
    assert any(s.type == "vmess" for s in servers)
    assert any(s.type == "unknown" for s in servers)
    # Проверяем, что emoji и query-параметры не ломают парсер
    vless = next((s for s in servers if s.type == "vless"), None)
    assert vless is not None
    # Проверяем что есть хотя бы один сервер с emoji или специальными символами в label/tag
    has_emoji_or_special = any(
        any(
            char in (s.meta.get("label", "") + s.meta.get("tag", ""))
            for char in ["🇳🇱", "🙀", "emoji", "VLESS", "WS"]
        )
        for s in servers
    )
    assert (
        has_emoji_or_special
    ), "Должен быть хотя бы один сервер с emoji или специальными символами"
    # Проверяем, что ошибки корректно отражаются в meta
    for s in servers:
        if s.address == "invalid":
            assert "error" in s.meta
