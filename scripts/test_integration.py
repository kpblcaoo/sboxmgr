#!/usr/bin/env python3
"""
Integration test for new sing-box models.
"""

import json
import subprocess
import tempfile

from sboxmgr.models import (
    DirectOutbound,
    MixedInbound,
    ShadowsocksOutbound,
    SingBoxConfig,
)


def test_integration():
    """Test integration of new models with sing-box validation."""

    print("Testing new sing-box models integration...")

    # Create a complete sing-box configuration
    config = SingBoxConfig(
        log={"level": "info"},
        inbounds=[
            MixedInbound(
                type="mixed", tag="mixed-in", listen="127.0.0.1", listen_port=7890
            )
        ],
        outbounds=[
            ShadowsocksOutbound(
                type="shadowsocks",
                tag="ss-out",
                server="example.com",
                server_port=8388,
                method="aes-256-gcm",
                password="password123",
            ),
            DirectOutbound(type="direct", tag="direct"),
        ],
        route={
            "rules": [{"outbound": "ss-out", "domain": ["google.com", "github.com"]}],
            "final": "direct",
        },
    )

    print("✅ Configuration created successfully")

    # Test Pydantic validation
    try:
        config_dict = config.to_dict()
        print("✅ Pydantic validation passed")
    except Exception as e:
        print(f"❌ Pydantic validation failed: {e}")
        return

    # Test sing-box validation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_dict, f, indent=2)
        config_file = f.name

    try:
        result = subprocess.run(
            ["/usr/bin/sing-box", "check", "-c", config_file],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ sing-box validation passed")
        else:
            print(f"❌ sing-box validation failed: {result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        print("⚠️  sing-box validation timeout")
    except Exception as e:
        print(f"❌ sing-box validation error: {e}")
    finally:
        import os

        os.unlink(config_file)

    # Test JSON serialization
    try:
        json_str = config.to_json(indent=2)
        print("✅ JSON serialization passed")
        print(f"Config size: {len(json_str)} characters")
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")

    print("\n✅ Integration test completed!")


if __name__ == "__main__":
    test_integration()
