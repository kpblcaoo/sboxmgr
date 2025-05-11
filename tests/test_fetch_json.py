from update_singbox import validate_protocol
import pytest

def test_validate_protocol_vless():
    config = {
        "protocol": "vless",
        "settings": {
            "vnext": [{"address": "1.1.1.1", "port": 443, "users": [{"id": "uuid123"}]}]
        }
    }
    outbound = validate_protocol(config)
    assert outbound["type"] == "vless"
    assert outbound["server"] == "1.1.1.1"
    assert outbound["server_port"] == 443
    assert outbound["uuid"] == "uuid123"

def test_validate_protocol_unsupported():
    config = {"protocol": "unsupported"}
    with pytest.raises(SystemExit) as excinfo:
        validate_protocol(config)
    assert "Unsupported protocol" in str(excinfo.value)