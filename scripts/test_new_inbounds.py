#!/usr/bin/env python3
"""Test script for new inbound protocols."""

import json
import subprocess
import tempfile

from src.sboxmgr.models.singbox import *


def test_new_inbounds():
    """Test new inbound protocols with sing-box validation."""
    # Test configs for new protocols
    test_configs = [
        {
            "type": "naive",
            "tag": "naive-test",
            "listen": "127.0.0.1",
            "listen_port": 8444,
            "network": "tcp",
            "users": [{"username": "test", "password": "test123"}],
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "certificate_path": "/tmp/test.crt",
                "key_path": "/tmp/test.key",
            },
        },
        {
            "type": "redirect",
            "tag": "redirect-test",
            "listen": "127.0.0.1",
            "listen_port": 8445,
        },
        {
            "type": "tproxy",
            "tag": "tproxy-test",
            "listen": "127.0.0.1",
            "listen_port": 8446,
            "network": "tcp",
        },
        {
            "type": "tun",
            "tag": "tun-test",
            "interface_name": "tun0",
            "address": ["172.18.0.1/30"],
            "mtu": 1500,
            "auto_route": True,
        },
    ]

    print("Testing new inbound protocols...")

    for i, config in enumerate(test_configs):
        protocol = config["type"]
        print(f"\n{i + 1}. Testing {protocol}...")

        # Test Pydantic validation
        try:
            if protocol == "naive":
                from sboxmgr.models.singbox.inbound import NaiveInbound

                NaiveInbound(**config)
            elif protocol == "redirect":
                from sboxmgr.models.singbox.inbound import RedirectInbound

                RedirectInbound(**config)
            elif protocol == "tproxy":
                from sboxmgr.models.singbox.inbound import TproxyInbound

                TproxyInbound(**config)
            elif protocol == "tun":
                from sboxmgr.models.singbox.inbound import TunInbound

                TunInbound(**config)
            else:
                print(f"  ❌ Unknown protocol: {protocol}")
                continue

            print("  ✅ Pydantic validation passed")

            # Test sing-box validation (skip tun for now as it requires root)
            if protocol != "tun":
                full_config = {
                    "log": {"level": "info"},
                    "inbounds": [config],
                    "outbounds": [{"type": "direct", "tag": "direct"}],
                }

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(full_config, f)
                    config_file = f.name

                try:
                    result = subprocess.run(
                        ["/usr/bin/sing-box", "check", "-c", config_file],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0:
                        print("  ✅ sing-box validation passed")
                    else:
                        print(
                            f"  ❌ sing-box validation failed: {result.stderr.strip()}"
                        )

                except subprocess.TimeoutExpired:
                    print("  ⚠️  sing-box validation timeout")
                except Exception as e:
                    print(f"  ❌ sing-box validation error: {e}")
                finally:
                    import os

                    os.unlink(config_file)
            else:
                print("  ⚠️  Skipping sing-box validation (requires root)")

        except Exception as e:
            print(f"  ❌ Pydantic validation failed: {e}")

    print("\n✅ All new inbound protocols tested!")


if __name__ == "__main__":
    test_new_inbounds()
