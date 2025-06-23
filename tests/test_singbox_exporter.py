from sboxmgr.subscription.exporters.singbox_exporter import SingboxExporter
from sboxmgr.subscription.models import ParsedServer

def test_singbox_exporter():
    servers = [
        ParsedServer(type="vmess", address="example.com", port=443, security="auto", meta={"uuid": "0000"}),  # pragma: allowlist secret
        ParsedServer(type="ss", address="127.0.0.1", port=8388, security="aes-256-gcm", meta={"password": "pass"}),  # pragma: allowlist secret
    ]
    exporter = SingboxExporter()
    config_json = exporter.export(servers)
    assert "outbounds" in config_json
    assert "example.com" in config_json
    assert "127.0.0.1" in config_json 