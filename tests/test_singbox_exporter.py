from sboxmgr.subscription.exporters.singbox_exporter import singbox_export
from sboxmgr.subscription.models import ParsedServer
import json

def test_singbox_exporter():
    servers = [
        ParsedServer(type="vmess", address="example.com", port=443, security="auto", meta={"uuid": "0000"}),  # pragma: allowlist secret
        ParsedServer(type="ss", address="127.0.0.1", port=8388, security="aes-256-gcm", meta={"password": "pass"}),  # pragma: allowlist secret
    ]
    config = singbox_export(servers, routes=[])
    config_json = json.dumps(config)
    assert "outbounds" in config_json
    assert "example.com" in config_json
    assert "127.0.0.1" in config_json 