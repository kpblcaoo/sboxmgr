#!/usr/bin/env python3
"""Debug script for EncryptionPolicy issue."""

from src.sboxmgr.policies.utils import extract_metadata_field

class MockServer:
    """Mock server object for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Тестовые данные из разных парсеров
test_cases = [
    {
        "name": "SingBoxParser (SFI User-Agent)",
        "server": MockServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            security="none",  # Слабое шифрование
            meta={
                "uuid": "031161a4-ba77-4592-8dd6-25f7d79110af",
                "security": "none",
                "flow": "xtls-rprx-vision",
                "tag": "🇳🇱 kpblcaoo Nederland-3",
                "origin": "singbox",
                "chain": "outbound",
                "server_id": "vless_4"
            }
        )
    },
    {
        "name": "Base64Parser (no User-Agent)",
        "server": MockServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            security="reality",  # Сильное шифрование
            meta={
                "uuid": "031161a4-ba77-4592-8dd6-25f7d79110af",
                "label": "🇳🇱 kpblcaoo Nederland-3",
                "security": "reality",
                "type": "tcp",
                "flow": "xtls-rprx-vision",
                "sni": "media-nl3.goodmc.org",
                "fp": "chrome",
                "pbk": "erru8JuvJBs-npGWA8ppjsh9GVjwGpoqsKzAYX8vIi8",  # pragma: allowlist secret
                "sid": "1b326693"
            }
        )
    },
    {
        "name": "ClashParser (default User-Agent)",
        "server": MockServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            security=None,  # None, но есть reality-opts
            meta={
                "name": "🇳🇱 kpblcaoo Nederland-3",
                "type": "vless",
                "server": "192.142.18.243",
                "port": 443,
                "network": "tcp",
                "udp": True,
                "tls": True,
                "servername": "media-nl3.goodmc.org",
                "reality-opts": {
                    "public-key": "erru8JuvJBs-npGWA8ppjsh9GVjwGpoqsKzAYX8vIi8",  # pragma: allowlist secret
                    "short-id": "1b326693"
                },
                "client-fingerprint": "chrome",
                "uuid": "031161a4-ba77-4592-8dd6-25f7d79110af",
                "flow": "xtls-rprx-vision"
            }
        )
    }
]

def test_extract_encryption():
    """Test encryption field extraction."""
    print("🔍 Testing EncryptionPolicy field extraction\n")
    
    for case in test_cases:
        print(f"📋 {case['name']}")
        server = case['server']
        
        # Test direct field extraction
        security = extract_metadata_field(server, "security")
        print(f"  security field: {security}")
        
        # Test fallback fields
        encryption = extract_metadata_field(server, "encryption", fallback_fields=["security", "cipher", "method"])
        print(f"  encryption (with fallbacks): {encryption}")
        
        # Test meta extraction
        meta_security = extract_metadata_field(server, "security", fallback_fields=[])
        print(f"  meta.security: {meta_security}")
        
        # Test reality detection
        has_tls = server.meta.get('tls') if hasattr(server, 'meta') else None
        has_reality_opts = server.meta.get('reality-opts') if hasattr(server, 'meta') else None
        print(f"  has tls: {has_tls}")
        print(f"  has reality-opts: {has_reality_opts}")
        
        print()

if __name__ == "__main__":
    test_extract_encryption() 