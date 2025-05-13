import pytest
from modules.protocol_validation import validate_protocol

def test_validate_protocol_valid():
    # Пример теста для проверки валидного протокола
    protocol = {
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": "example.com",
                    "port": 443,
                    "users": [
                        {"id": "uuid-example"}
                    ]
                }
            ]
        }
    }
    supported_protocols = ["vless", "http"]
    assert validate_protocol(protocol, supported_protocols) is not None

def test_validate_protocol_invalid():
    # Пример теста для проверки невалидного протокола
    protocol = {"protocol": "unknown"}
    supported_protocols = ["vless", "http"]
    with pytest.raises(ValueError):
        validate_protocol(protocol, supported_protocols)
