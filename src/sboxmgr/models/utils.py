"""Utility models for SBoxMgr."""

import json
from pathlib import Path
from pydantic import ValidationError
from .config import SingBoxConfig

def validate_singbox_config(config_path: Path) -> bool:
    """Validate sing-box configuration file."""
    try:
        config_data = json.loads(config_path.read_text())
        SingBoxConfig.model_validate(config_data)
        print("✅ Configuration validated successfully")
        return True
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"❌ Validation failed: {e}")
        return False

def generate_singbox_schema(output_path: Path) -> None:
    """Generate JSON Schema for sing-box configuration."""
    schema = SingBoxConfig.generate_schema()
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"✅ Schema generated: {output_path}")

def create_example_config() -> dict:
    """Create an example sing-box configuration for testing."""
    return {
        "log": {"level": "info", "timestamp": True},
        "dns": {
            "servers": [{"tag": "google", "address": "8.8.8.8", "strategy": "prefer_ipv4"}],
            "rules": [{"type": "default", "domain": ["example.com"], "server": "google"}],
            "final": "google"
        },
        "ntp": {"enabled": True, "server": "pool.ntp.org", "server_port": 123},
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": 1080,
                "users": [{"username": "user", "password": "pass"}]
            }
        ],
        "outbounds": [
            {
                "type": "shadowsocks",
                "tag": "ss-out",
                "server": "example.com",
                "server_port": 8388,
                "method": "aes-256-gcm",
                "password": "secret",
                "network": "tcp_udp"
            },
            {
                "type": "vmess",
                "tag": "vmess-out",
                "server": "example.com",
                "server_port": 10086,
                "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
                "security": "auto",
                "alter_id": 4,
                "transport": {"network": "ws", "ws_opts": {"path": "/ws"}}
            },
            {
                "type": "hysteria2",
                "tag": "hysteria2-out",
                "server": "example.com",
                "server_port": 443,
                "password": "secret",
                "obfs": "salamander",
                "obfs_type": "salamander",
                "tls": {
                    "enabled": True,
                    "server_name": "example.com"
                }
            }
        ],
        "route": {
            "rules": [{"type": "default", "domain": ["example.com"], "outbound": "ss-out"}],
            "final": "ss-out"
        }
    } 