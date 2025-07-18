#!/usr/bin/env python3
"""Demonstration of Phase 3 PostProcessor Architecture.

This script demonstrates the enhanced postprocessor architecture with
profile integration, middleware support, and advanced features introduced
in Phase 3 of the architectural improvements.

Features demonstrated:
- Profile-aware postprocessors
- PostProcessor chains with different execution strategies
- Middleware integration (logging, enrichment)
- Error handling and recovery
- Metadata collection and performance monitoring
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


from sboxmgr.configs.models import FilterProfile, FullProfile
from sboxmgr.subscription.models import ParsedServer, PipelineContext
from sboxmgr.subscription.postprocessors import (
    GeoFilterPostProcessor,
    LatencySortPostProcessor,
    PostProcessorChain,
    TagFilterPostProcessor,
)

# Initialize logging for middleware
try:
    from sboxmgr.logging.core import initialize_logging

    initialize_logging()
    from sboxmgr.subscription.middleware import EnrichmentMiddleware, LoggingMiddleware

    MIDDLEWARE_AVAILABLE = True
except Exception as e:
    print(f"Warning: Middleware not available: {e}")
    MIDDLEWARE_AVAILABLE = False


def create_sample_servers() -> list[ParsedServer]:
    """Create sample servers for demonstration."""
    return [
        ParsedServer(
            type="vmess",
            address="us-server-1.example.com",
            port=443,
            tag="US-Premium-Fast",
            meta={"country": "US", "latency_ms": 45, "provider": "Premium"},
        ),
        ParsedServer(
            type="shadowsocks",
            address="ca-server-1.example.com",
            port=8080,
            tag="CA-Basic-Medium",
            meta={"country": "CA", "latency_ms": 120, "provider": "Basic"},
        ),
        ParsedServer(
            type="trojan",
            address="uk-server-1.example.com",
            port=443,
            tag="UK-Premium-Fast",
            meta={"country": "UK", "latency_ms": 65, "provider": "Premium"},
        ),
        ParsedServer(
            type="vless",
            address="de-server-1.example.com",
            port=443,
            tag="DE-Premium-Slow",
            meta={"country": "DE", "latency_ms": 200, "provider": "Premium"},
        ),
        ParsedServer(
            type="wireguard",
            address="jp-server-1.example.com",
            port=51820,
            tag="JP-Basic-Fast",
            meta={"country": "JP", "latency_ms": 80, "provider": "Basic"},
        ),
        ParsedServer(
            type="vmess",
            address="blocked-server.example.com",
            port=443,
            tag="Blocked-Server",
            meta={"country": "CN", "latency_ms": 500, "provider": "Blocked"},
        ),
    ]


def create_sample_profile() -> FullProfile:
    """Create a sample profile for demonstration."""
    filter_profile = FilterProfile(
        only_tags=["Premium", "Fast"],
        exclude_tags=["Blocked"],
        exclusions=["blocked-server.example.com"],
    )

    # Create a minimal profile - we'll need to adjust based on actual FullProfile structure
    profile = FullProfile(id="demo-profile", filters=filter_profile)

    # Add custom metadata for postprocessors
    profile.metadata = {
        "geo_filter": {
            "allowed_countries": ["US", "CA", "UK", "DE", "JP"],
            "blocked_countries": ["CN"],
            "fallback_mode": "block",
        },
        "latency_sort": {
            "sort_order": "asc",
            "max_latency_ms": 150,
            "measurement_method": "cached",
        },
        "logging": {
            "log_level": "info",
            "log_server_details": True,
            "log_performance": True,
        },
        "enrichment": {
            "enable_geo_enrichment": True,
            "enable_performance_enrichment": True,
            "enable_security_enrichment": True,
        },
    }

    return profile


def demo_individual_postprocessors():
    """Demonstrate individual postprocessor functionality."""
    print("=" * 60)
    print("DEMO: Individual PostProcessors")
    print("=" * 60)

    servers = create_sample_servers()
    profile = create_sample_profile()
    context = PipelineContext(source="demo", debug_level=1)

    print(f"Starting with {len(servers)} servers:")
    for server in servers:
        print(f"  - {server.tag} ({server.type}://{server.address}:{server.port})")

    # Demonstrate GeoFilterPostProcessor
    print("\n1. Geographic Filtering:")
    geo_filter = GeoFilterPostProcessor(
        {
            "allowed_countries": ["US", "CA", "UK"],
            "blocked_countries": ["CN"],
            "fallback_mode": "block",
        }
    )

    geo_filtered = geo_filter.process(servers, context, profile)
    print(f"   After geo filtering: {len(geo_filtered)} servers")
    for server in geo_filtered:
        country = server.meta.get("country", "Unknown")
        print(f"   - {server.tag} ({country})")

    # Demonstrate TagFilterPostProcessor with more inclusive settings
    print("\n2. Tag-based Filtering:")
    tag_filter = TagFilterPostProcessor(
        {
            "include_tags": ["Premium", "Basic"],  # Include both Premium and Basic
            "exclude_tags": ["Blocked"],
            "case_sensitive": False,
            "fallback_mode": "allow",  # Allow servers without matching tags
        }
    )

    tag_filtered = tag_filter.process(geo_filtered, context, profile)
    print(f"   After tag filtering: {len(tag_filtered)} servers")
    for server in tag_filtered:
        print(f"   - {server.tag}")

    # Demonstrate LatencySortPostProcessor
    print("\n3. Latency-based Sorting:")
    latency_sort = LatencySortPostProcessor(
        {"sort_order": "asc", "measurement_method": "cached"}
    )

    sorted_servers = latency_sort.process(tag_filtered, context, profile)
    print(f"   After latency sorting: {len(sorted_servers)} servers")
    for server in sorted_servers:
        latency = server.meta.get("latency_ms", "Unknown")
        print(f"   - {server.tag} ({latency}ms)")


def demo_postprocessor_chain():
    """Demonstrate PostProcessor chain functionality."""
    print("\n" + "=" * 60)
    print("DEMO: PostProcessor Chain")
    print("=" * 60)

    servers = create_sample_servers()
    profile = create_sample_profile()
    context = PipelineContext(source="demo-chain", debug_level=1)

    # Create postprocessor chain with more inclusive settings
    processors = [
        GeoFilterPostProcessor(
            {
                "allowed_countries": ["US", "CA", "UK", "DE", "JP"],
                "blocked_countries": ["CN"],
            }
        ),
        TagFilterPostProcessor(
            {
                "include_tags": ["Premium", "Basic"],
                "exclude_tags": ["Blocked"],
                "fallback_mode": "allow",
            }
        ),
        LatencySortPostProcessor(
            {
                "sort_order": "asc",
                "max_latency_ms": 300,  # Allow higher latency for demo
                "measurement_method": "cached",
            }
        ),
    ]

    # Sequential execution
    print("\n1. Sequential Execution:")
    chain = PostProcessorChain(
        processors,
        {
            "execution_mode": "sequential",
            "error_strategy": "continue",
            "collect_metadata": True,
        },
    )

    result = chain.process(servers, context, profile)
    print(f"   Final result: {len(result)} servers")
    for server in result:
        latency = server.meta.get("latency_ms", "Unknown")
        country = server.meta.get("country", "Unknown")
        print(f"   - {server.tag} ({country}, {latency}ms)")

    # Print execution metadata
    metadata = chain.get_metadata()
    exec_meta = metadata.get("execution_metadata", {})
    print("\n   Execution metadata:")
    print(f"   - Processors executed: {len(exec_meta.get('processors_executed', []))}")
    print(f"   - Processors failed: {len(exec_meta.get('processors_failed', []))}")
    print(f"   - Duration: {exec_meta.get('duration', 0):.3f} seconds")


def demo_middleware_integration():
    """Demonstrate middleware integration."""
    if not MIDDLEWARE_AVAILABLE:
        print("\n" + "=" * 60)
        print("DEMO: Middleware Integration (SKIPPED)")
        print("=" * 60)
        print("Middleware not available due to logging initialization issues.")
        print("This is expected in demo environment.")
        return

    print("\n" + "=" * 60)
    print("DEMO: Middleware Integration")
    print("=" * 60)

    servers = create_sample_servers()
    profile = create_sample_profile()
    context = PipelineContext(source="demo-middleware", debug_level=1)

    # Create middleware components
    logging_middleware = LoggingMiddleware(
        {
            "log_level": "info",
            "log_server_details": True,
            "log_performance": True,
            "max_servers_logged": 3,
        }
    )

    enrichment_middleware = EnrichmentMiddleware(
        {
            "enable_geo_enrichment": True,
            "enable_performance_enrichment": True,
            "enable_security_enrichment": True,
        }
    )

    print("\n1. Applying Logging Middleware:")
    logged_servers = logging_middleware.process(servers, context, profile)
    print(f"   Processed {len(logged_servers)} servers with logging")

    print("\n2. Applying Enrichment Middleware:")
    enriched_servers = enrichment_middleware.process(logged_servers, context, profile)
    print(f"   Enriched {len(enriched_servers)} servers")

    # Show enrichment results
    for server in enriched_servers[:3]:  # Show first 3
        print(f"   - {server.tag}:")
        if "enriched_at" in server.meta:
            print(f"     * Enriched at: {server.meta['enriched_at']}")
        if "server_id" in server.meta:
            print(f"     * Server ID: {server.meta['server_id']}")
        if "performance" in server.meta:
            perf = server.meta["performance"]
            print(
                f"     * Performance: {perf.get('estimated_latency_class', 'unknown')} latency"
            )
        if "security" in server.meta:
            sec = server.meta["security"]
            print(
                f"     * Security: {sec.get('encryption_level', 'unknown')} encryption"
            )


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "=" * 60)
    print("DEMO: Error Handling")
    print("=" * 60)

    servers = create_sample_servers()
    context = PipelineContext(source="demo-errors", debug_level=1)

    # Create a processor that will fail
    class FailingProcessor(GeoFilterPostProcessor):
        def process(self, servers, context=None, profile=None):
            raise Exception("Simulated processor failure")

    # Create chain with failing processor
    processors = [
        GeoFilterPostProcessor({"allowed_countries": ["US", "CA"]}),
        FailingProcessor(),  # This will fail
        LatencySortPostProcessor({"sort_order": "asc"}),
    ]

    print("\n1. Error Handling with 'continue' strategy:")
    chain = PostProcessorChain(
        processors,
        {
            "execution_mode": "sequential",
            "error_strategy": "continue",
            "collect_metadata": True,
        },
    )

    result = chain.process(servers, context)
    print(f"   Result: {len(result)} servers (processing continued despite error)")

    # Show error metadata
    metadata = chain.get_metadata()
    exec_meta = metadata.get("execution_metadata", {})
    failed = exec_meta.get("processors_failed", [])
    if failed:
        print(f"   Failed processors: {len(failed)}")
        for failure in failed:
            print(f"   - {failure['name']}: {failure['error']}")


def main():
    """Run all demonstrations."""
    print("Phase 3 PostProcessor Architecture Demonstration")
    print("=" * 60)
    print("This demo showcases the enhanced postprocessor architecture")
    print("with profile integration, middleware, and advanced features.")

    try:
        demo_individual_postprocessors()
        demo_postprocessor_chain()
        demo_middleware_integration()
        demo_error_handling()

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey features demonstrated:")
        print("✓ Profile-aware postprocessors")
        print("✓ Geographic and tag-based filtering")
        print("✓ Latency-based sorting")
        print("✓ PostProcessor chains with different execution strategies")
        if MIDDLEWARE_AVAILABLE:
            print("✓ Middleware integration (logging, enrichment)")
        else:
            print("⚠ Middleware integration (skipped due to logging setup)")
        print("✓ Error handling and recovery")
        print("✓ Metadata collection and performance monitoring")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
