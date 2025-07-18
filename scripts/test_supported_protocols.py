#!/usr/bin/env python3
"""
Test which protocols are actually supported by our sing-box version.
"""

import json
import subprocess
import tempfile
from pathlib import Path


def test_protocol_support():
    """Test which protocols are supported by sing-box."""

    # Known protocols from documentation
    outbound_protocols = [
        "vless",
        "vmess",
        "shadowsocks",
        "trojan",
        "direct",
        "block",
        "http",
        "socks",
        "dns",
        "selector",
        "urltest",
        "wireguard",
        "hysteria",
        "hysteria2",
        "tuic",
        "ssh",
        "tor",
        "shadowtls",
        "anytls",
    ]

    inbound_protocols = [
        "http",
        "socks",
        "mixed",
        "tun",
        "redirect",
        "tproxy",
        "shadowsocks",
        "vmess",
        "vless",
        "trojan",
        "hysteria",
        "hysteria2",
        "tuic",
        "naive",
        "shadowtls",
        "anytls",
        "direct",
    ]

    print("🔍 TESTING PROTOCOL SUPPORT")
    print("=" * 50)

    supported_outbounds = []
    supported_inbounds = []

    # Test outbound protocols
    print("\n🌐 TESTING OUTBOUND PROTOCOLS:")
    for protocol in outbound_protocols:
        config = {
            "log": {"level": "error"},
            "outbounds": [{"type": protocol, "tag": "test"}],
            "route": {"final": "test"},
        }

        # Add required fields for specific protocols
        if protocol == "vless":
            config["outbounds"][0].update(
                {
                    "server": "127.0.0.1",
                    "server_port": 443,
                    "uuid": "00000000-0000-0000-0000-000000000000",
                }
            )
        elif protocol == "vmess":
            config["outbounds"][0].update(
                {
                    "server": "127.0.0.1",
                    "server_port": 443,
                    "uuid": "00000000-0000-0000-0000-000000000000",
                }
            )
        elif protocol == "shadowsocks":
            config["outbounds"][0].update(
                {
                    "server": "127.0.0.1",
                    "server_port": 443,
                    "method": "aes-256-gcm",
                    "password": "test",
                }
            )
        elif protocol == "trojan":
            config["outbounds"][0].update(
                {"server": "127.0.0.1", "server_port": 443, "password": "test"}
            )
        elif protocol == "selector":
            config["outbounds"][0].update({"outbounds": ["test"], "default": "test"})
        elif protocol == "urltest":
            config["outbounds"][0].update(
                {
                    "outbounds": ["test"],
                    "url": "https://www.google.com/generate_204",
                    "interval": "1m",
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f, indent=2)
            config_path = f.name

        try:
            result = subprocess.run(
                ["sing-box", "check", "-c", config_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(f"  ✅ {protocol}")
                supported_outbounds.append(protocol)
            else:
                # Check if it's just missing required fields or unsupported
                if (
                    "unknown" in result.stderr.lower()
                    or "unsupported" in result.stderr.lower()
                ):
                    print(f"  ❌ {protocol} (unsupported)")
                else:
                    print(f"  ⚠️  {protocol} (missing fields)")
                    supported_outbounds.append(protocol)

        except subprocess.TimeoutExpired:
            print(f"  ⏰ {protocol} (timeout)")
        except Exception as e:
            print(f"  💥 {protocol} (error: {e})")
        finally:
            Path(config_path).unlink()

    # Test inbound protocols
    print("\n🌐 TESTING INBOUND PROTOCOLS:")
    for protocol in inbound_protocols:
        config = {
            "log": {"level": "error"},
            "inbounds": [{"type": protocol, "tag": "test"}],
            "outbounds": [{"type": "direct", "tag": "direct"}],
            "route": {"final": "direct"},
        }

        # Add required fields for specific protocols
        if protocol in ["http", "socks", "mixed"]:
            config["inbounds"][0].update({"listen": "127.0.0.1", "listen_port": 8080})
        elif protocol == "shadowsocks":
            config["inbounds"][0].update(
                {
                    "listen": "127.0.0.1",
                    "listen_port": 8080,
                    "method": "aes-256-gcm",
                    "password": "test",
                }
            )
        elif protocol == "vmess":
            config["inbounds"][0].update(
                {
                    "listen": "127.0.0.1",
                    "listen_port": 8080,
                    "users": [{"uuid": "00000000-0000-0000-0000-000000000000"}],
                }
            )
        elif protocol == "vless":
            config["inbounds"][0].update(
                {
                    "listen": "127.0.0.1",
                    "listen_port": 8080,
                    "users": [{"uuid": "00000000-0000-0000-0000-000000000000"}],
                }
            )
        elif protocol == "trojan":
            config["inbounds"][0].update(
                {
                    "listen": "127.0.0.1",
                    "listen_port": 8080,
                    "users": [{"password": "test"}],
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f, indent=2)
            config_path = f.name

        try:
            result = subprocess.run(
                ["sing-box", "check", "-c", config_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(f"  ✅ {protocol}")
                supported_inbounds.append(protocol)
            else:
                # Check if it's just missing required fields or unsupported
                if (
                    "unknown" in result.stderr.lower()
                    or "unsupported" in result.stderr.lower()
                ):
                    print(f"  ❌ {protocol} (unsupported)")
                else:
                    print(f"  ⚠️  {protocol} (missing fields)")
                    supported_inbounds.append(protocol)

        except subprocess.TimeoutExpired:
            print(f"  ⏰ {protocol} (timeout)")
        except Exception as e:
            print(f"  💥 {protocol} (error: {e})")
        finally:
            Path(config_path).unlink()

    # Summary
    print("\n📊 SUMMARY:")
    print(
        f"  Supported outbounds: {len(supported_outbounds)}/{len(outbound_protocols)}"
    )
    print(f"  Supported inbounds: {len(supported_inbounds)}/{len(inbound_protocols)}")
    print(
        f"  Total supported: {len(supported_outbounds) + len(supported_inbounds)}/{len(outbound_protocols) + len(inbound_protocols)}"
    )

    print("\n✅ SUPPORTED OUTBOUNDS:")
    for protocol in sorted(supported_outbounds):
        print(f"  - {protocol}")

    print("\n✅ SUPPORTED INBOUNDS:")
    for protocol in sorted(supported_inbounds):
        print(f"  - {protocol}")

    return {
        "supported_outbounds": supported_outbounds,
        "supported_inbounds": supported_inbounds,
        "total_supported": len(supported_outbounds) + len(supported_inbounds),
    }


if __name__ == "__main__":
    test_protocol_support()
