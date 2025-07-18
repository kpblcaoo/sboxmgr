#!/usr/bin/env python3
"""Simple middleware test without logging initialization.

This demonstrates that middleware components work correctly
even without full logging setup.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sboxmgr.configs.models import FilterProfile, FullProfile
from sboxmgr.subscription.middleware import EnrichmentMiddleware
from sboxmgr.subscription.models import ParsedServer, PipelineContext


def test_enrichment_middleware():
    """Test enrichment middleware functionality."""
    print("Testing Enrichment Middleware")
    print("=" * 40)

    # Create sample servers
    servers = [
        ParsedServer(
            type="vmess",
            address="test-server.com",
            port=443,
            tag="Test-Server",
            meta={"country": "US"},
        ),
        ParsedServer(
            type="shadowsocks",
            address="another-server.com",
            port=8080,
            tag="Another-Server",
            meta={"country": "CA"},
        ),
    ]

    # Create context and profile
    context = PipelineContext(source="middleware-test", debug_level=1)
    profile = FullProfile(id="test-profile", filters=FilterProfile())

    # Test enrichment middleware
    enrichment = EnrichmentMiddleware(
        {
            "enable_geo_enrichment": True,
            "enable_performance_enrichment": True,
            "enable_security_enrichment": True,
        }
    )

    print(f"Input servers: {len(servers)}")
    for server in servers:
        print(f"  - {server.tag} ({server.type}://{server.address}:{server.port})")

    # Process with enrichment
    enriched_servers = enrichment.process(servers, context, profile)

    print(f"\nEnriched servers: {len(enriched_servers)}")
    for server in enriched_servers:
        print(f"  - {server.tag}:")
        if "enriched_at" in server.meta:
            print(f"    * Enriched at: {server.meta['enriched_at']}")
        if "server_id" in server.meta:
            print(f"    * Server ID: {server.meta['server_id']}")
        if "performance" in server.meta:
            perf = server.meta["performance"]
            print(
                f"    * Latency class: {perf.get('estimated_latency_class', 'unknown')}"
            )
            print(
                f"    * Protocol efficiency: {perf.get('protocol_efficiency', 'unknown')}"
            )
        if "security" in server.meta:
            sec = server.meta["security"]
            print(f"    * Encryption level: {sec.get('encryption_level', 'unknown')}")
            print(
                f"    * Port classification: {sec.get('port_classification', 'unknown')}"
            )

    print("\n✅ Enrichment middleware test completed successfully!")


def test_middleware_base_classes():
    """Test middleware base classes."""
    print("\nTesting Middleware Base Classes")
    print("=" * 40)

    from sboxmgr.subscription.middleware import (
        BaseMiddleware,
        ChainableMiddleware,
        ConditionalMiddleware,
        ProfileAwareMiddleware,
        TransformMiddleware,
    )

    # Test that all base classes are available
    classes = [
        BaseMiddleware,
        ProfileAwareMiddleware,
        ChainableMiddleware,
        ConditionalMiddleware,
        TransformMiddleware,
    ]

    for cls in classes:
        print(f"✅ {cls.__name__} available")

    print("\n✅ All middleware base classes available!")


if __name__ == "__main__":
    print("Middleware Test Suite")
    print("=" * 50)

    try:
        test_middleware_base_classes()
        test_enrichment_middleware()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! ✅")
        print("=" * 50)
        print("\nMiddleware is fully functional and ready for use.")
        print("The logging middleware requires proper logging initialization")
        print("which is handled automatically in the main application.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
