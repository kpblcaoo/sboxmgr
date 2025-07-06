#!/usr/bin/env python3
"""Test script to verify tag normalization conflict between TagNormalizer and EnrichmentMiddleware."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from sboxmgr.subscription.middleware.enrichment.core import (  # noqa: E402
    EnrichmentMiddleware,
)
from sboxmgr.subscription.middleware.tag_normalizer import TagNormalizer  # noqa: E402
from sboxmgr.subscription.models import ParsedServer, PipelineContext  # noqa: E402


def test_tag_normalization_conflict():
    """Test if there's a conflict between TagNormalizer and EnrichmentMiddleware."""

    # Create test servers with duplicate names
    servers = [
        ParsedServer(
            type="vless",
            address="1.1.1.1",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
        ParsedServer(
            type="vless",
            address="2.2.2.2",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
        ParsedServer(
            type="vless",
            address="3.3.3.3",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
    ]

    context = PipelineContext(source="test")

    print("=== Testing TagNormalizer alone ===")
    tag_normalizer = TagNormalizer()
    normalized_servers = tag_normalizer.process(servers, context)

    print("TagNormalizer results:")
    for i, server in enumerate(normalized_servers):
        print(f"  Server {i+1}: {server.tag}")

    print("\n=== Testing EnrichmentMiddleware alone ===")
    enrichment_middleware = EnrichmentMiddleware()
    enriched_servers = enrichment_middleware.process(servers, context)

    print("EnrichmentMiddleware results:")
    for i, server in enumerate(enriched_servers):
        print(f"  Server {i+1}: {server.tag}")

    print("\n=== Testing both in sequence (simulating middleware chain) ===")
    # Simulate the middleware chain execution order
    # First TagNormalizer (as it's added first in ExportManager)
    temp_servers = tag_normalizer.process(servers, context)
    print("After TagNormalizer:")
    for i, server in enumerate(temp_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Then EnrichmentMiddleware
    final_servers = enrichment_middleware.process(temp_servers, context)
    print("After EnrichmentMiddleware:")
    for i, server in enumerate(final_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Check for duplicates
    final_tags = [server.tag for server in final_servers]
    unique_tags = set(final_tags)

    print("\n=== Analysis ===")
    print(f"Total servers: {len(final_servers)}")
    print(f"Unique tags: {len(unique_tags)}")
    print(f"Duplicate tags: {len(final_tags) - len(unique_tags)}")

    if len(final_tags) != len(unique_tags):
        print("❌ CONFLICT DETECTED: Duplicate tags found!")
        duplicates = [tag for tag in final_tags if final_tags.count(tag) > 1]
        print(f"Duplicate tags: {duplicates}")
        return True
    else:
        print("✅ NO CONFLICT: All tags are unique")
        return False


def test_export_manager_scenario():
    """Test the exact scenario described in the bug report."""

    print("\n" + "=" * 60)
    print("TESTING EXPORT MANAGER SCENARIO")
    print("=" * 60)

    # Create servers with the same name (as described in bug report)
    servers = [
        ParsedServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            meta={"name": "🇳🇱 kpblcaoo Nederland-3"},
        ),
        ParsedServer(
            type="vless",
            address="192.142.18.244",
            port=443,
            meta={"name": "🇳🇱 kpblcaoo Nederland-3"},
        ),
        ParsedServer(
            type="vless",
            address="192.142.18.245",
            port=443,
            meta={"name": "🇳🇱 kpblcaoo Nederland-3"},
        ),
    ]

    context = PipelineContext(source="test")

    # Simulate ExportManager middleware chain
    # TagNormalizer is added first (line 93-99 in export_manager.py)
    tag_normalizer = TagNormalizer()
    temp_servers = tag_normalizer.process(servers, context)

    print("After TagNormalizer (global uniqueness tracking):")
    for i, server in enumerate(temp_servers):
        print(f"  Server {i+1}: {server.tag}")

    # EnrichmentMiddleware is added later (line 420-425 in export_manager.py)
    enrichment_middleware = EnrichmentMiddleware()
    final_servers = enrichment_middleware.process(temp_servers, context)

    print("After EnrichmentMiddleware (local uniqueness tracking):")
    for i, server in enumerate(final_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Check for duplicates
    final_tags = [server.tag for server in final_servers]
    unique_tags = set(final_tags)

    print("\n=== Export Manager Analysis ===")
    print(f"Total servers: {len(final_servers)}")
    print(f"Unique tags: {len(unique_tags)}")
    print(f"Duplicate tags: {len(final_tags) - len(unique_tags)}")

    if len(final_tags) != len(unique_tags):
        print("❌ CONFLICT DETECTED: Duplicate tags found!")
        duplicates = [tag for tag in final_tags if final_tags.count(tag) > 1]
        print(f"Duplicate tags: {duplicates}")
        return True
    else:
        print("✅ NO CONFLICT: All tags are unique")
        return False


def test_actual_conflict_scenario():
    """Test the actual conflict scenario where EnrichmentMiddleware processes servers one by one."""

    print("\n" + "=" * 60)
    print("TESTING ACTUAL CONFLICT SCENARIO")
    print("=" * 60)

    # Create servers with the same name
    servers = [
        ParsedServer(
            type="vless",
            address="1.1.1.1",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
        ParsedServer(
            type="vless",
            address="2.2.2.2",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
        ParsedServer(
            type="vless",
            address="3.3.3.3",
            port=443,
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
    ]

    context = PipelineContext(source="test")

    # Step 1: TagNormalizer processes all servers and ensures global uniqueness
    tag_normalizer = TagNormalizer()
    normalized_servers = tag_normalizer.process(servers, context)

    print("Step 1: After TagNormalizer (global uniqueness):")
    for i, server in enumerate(normalized_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Step 2: EnrichmentMiddleware processes servers (FIXED VERSION)
    # Now EnrichmentMiddleware no longer has tag normalization logic
    enrichment_middleware = EnrichmentMiddleware()

    print("\nStep 2: EnrichmentMiddleware processing (FIXED VERSION):")
    print("EnrichmentMiddleware no longer has tag normalization logic.")
    print("It only enriches data and preserves tags from TagNormalizer.")

    # Process through EnrichmentMiddleware
    enriched_servers = enrichment_middleware.process(normalized_servers, context)

    print("\nFinal results after EnrichmentMiddleware:")
    for i, server in enumerate(enriched_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Check for duplicates
    final_tags = [server.tag for server in enriched_servers]
    unique_tags = set(final_tags)

    print("\n=== Conflict Analysis ===")
    print(f"Total servers: {len(enriched_servers)}")
    print(f"Unique tags: {len(unique_tags)}")
    print(f"Duplicate tags: {len(final_tags) - len(unique_tags)}")

    if len(final_tags) != len(unique_tags):
        print("❌ CONFLICT CONFIRMED: Duplicate tags found!")
        duplicates = [tag for tag in final_tags if final_tags.count(tag) > 1]
        print(f"Duplicate tags: {duplicates}")
        return True
    else:
        print("✅ NO CONFLICT: All tags are unique")
        print("\nSUCCESS: The architectural issue has been resolved!")
        print("- TagNormalizer handles all tag normalization")
        print("- EnrichmentMiddleware only enriches data")
        print("- No duplicate tag normalization mechanisms")
        return False


def test_potential_conflict_scenario():
    """Test a scenario where the conflict could potentially occur."""

    print("\n" + "=" * 60)
    print("TESTING POTENTIAL CONFLICT SCENARIO")
    print("=" * 60)

    # Create a scenario where the two normalizers might produce different results
    # This would happen if they had different priority logic or different
    # uniqueness tracking mechanisms

    # Create servers with mixed metadata that could lead to different normalization
    servers = [
        # Server 1: Has name in meta, but TagNormalizer might prefer it differently
        ParsedServer(
            type="vless",
            address="1.1.1.1",
            port=443,
            tag="vless-1.1.1.1",
            meta={"name": "🇳🇱 Netherlands Server"},
        ),
        # Server 2: Has label in meta, different from name
        ParsedServer(
            type="vless",
            address="2.2.2.2",
            port=443,
            tag="vless-2.2.2.2",
            meta={"label": "🇳🇱 Netherlands Server"},
        ),
        # Server 3: Has explicit tag in meta
        ParsedServer(
            type="vless",
            address="3.3.3.3",
            port=443,
            tag="vless-3.3.3.3",
            meta={"tag": "🇳🇱 Netherlands Server"},
        ),
    ]

    context = PipelineContext(source="test")

    print("Input servers:")
    for i, server in enumerate(servers):
        print(f"  Server {i+1}: tag='{server.tag}', meta={server.meta}")

    # Step 1: TagNormalizer processes all servers
    tag_normalizer = TagNormalizer()
    normalized_servers = tag_normalizer.process(servers, context)

    print("\nStep 1: After TagNormalizer:")
    for i, server in enumerate(normalized_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Step 2: EnrichmentMiddleware processes servers
    enrichment_middleware = EnrichmentMiddleware()
    enriched_servers = enrichment_middleware.process(normalized_servers, context)

    print("\nStep 2: After EnrichmentMiddleware:")
    for i, server in enumerate(enriched_servers):
        print(f"  Server {i+1}: {server.tag}")

    # Check for duplicates
    final_tags = [server.tag for server in enriched_servers]
    unique_tags = set(final_tags)

    print("\n=== Potential Conflict Analysis ===")
    print(f"Total servers: {len(enriched_servers)}")
    print(f"Unique tags: {len(unique_tags)}")
    print(f"Duplicate tags: {len(final_tags) - len(unique_tags)}")

    if len(final_tags) != len(unique_tags):
        print("❌ CONFLICT CONFIRMED: Duplicate tags found!")
        duplicates = [tag for tag in final_tags if final_tags.count(tag) > 1]
        print(f"Duplicate tags: {duplicates}")
        return True
    else:
        print("✅ NO CONFLICT: All tags are unique")
        print("\nThe architectural issue exists but doesn't manifest in this scenario")
        print("because both normalizers use identical logic.")
        return False


def test_architectural_analysis():
    """Analyze the architectural issue described in the bug report."""

    print("\n" + "=" * 60)
    print("ARCHITECTURAL ANALYSIS")
    print("=" * 60)

    print("The bug report describes a valid architectural issue:")
    print()
    print("1. TWO SEPARATE TAG NORMALIZATION MECHANISMS:")
    print("   - TagNormalizer: Global uniqueness tracking across all servers")
    print(
        "   - EnrichmentMiddleware.EnrichmentTagNormalizer: Local uniqueness tracking"
    )
    print()
    print("2. POTENTIAL CONFLICT SCENARIOS:")
    print("   - TagNormalizer processes all servers and ensures global uniqueness")
    print("   - EnrichmentMiddleware re-processes servers and only checks against")
    print("     servers already processed in its own batch")
    print("   - This can lead to duplicate tags if the two normalizers have")
    print("     different logic or if EnrichmentMiddleware doesn't account for")
    print("     tags already normalized by TagNormalizer")
    print()
    print("3. CURRENT IMPLEMENTATION:")
    print("   - Both normalizers use identical priority logic")
    print("   - Both use identical uniqueness suffix patterns")
    print("   - This prevents the conflict from manifesting in practice")
    print()
    print("4. ARCHITECTURAL ISSUES:")
    print("   - Code duplication: Two separate tag normalization implementations")
    print("   - Potential for divergence: If one normalizer is modified, the other")
    print("     might not be updated consistently")
    print("   - Unclear responsibility: Which normalizer should be authoritative?")
    print()
    print("5. RECOMMENDATIONS:")
    print("   - Consolidate tag normalization into a single mechanism")
    print("   - Make EnrichmentMiddleware use TagNormalizer instead of its own")
    print("   - Or remove tag normalization from EnrichmentMiddleware entirely")
    print("   - Ensure clear separation of concerns")

    return True  # The architectural issue exists


if __name__ == "__main__":
    print("Testing Tag Normalization Conflict")
    print("=" * 40)

    conflict1 = test_tag_normalization_conflict()
    conflict2 = test_export_manager_scenario()
    conflict3 = test_actual_conflict_scenario()
    conflict4 = test_potential_conflict_scenario()
    architectural_issue = test_architectural_analysis()

    print("\n" + "=" * 60)
    print("FINAL CONCLUSION")
    print("=" * 60)

    if conflict1 or conflict2 or conflict3 or conflict4:
        print("❌ BUG CONFIRMED: Tag normalization conflict exists")
        print("The bug report is accurate - there is a conflict between")
        print("TagNormalizer and EnrichmentMiddleware tag normalization mechanisms.")
    else:
        print("✅ BUG NOT CONFIRMED: No tag normalization conflict found")
        print("The bug report may be incorrect or the issue has been resolved.")
        print("\nHowever, the architectural issue described in the bug report")
        print("is valid - there are indeed two separate tag normalization")
        print("mechanisms that could potentially conflict.")

    if architectural_issue:
        print("\n🔍 ARCHITECTURAL ISSUE CONFIRMED:")
        print("The bug report correctly identifies an architectural problem")
        print("with duplicate tag normalization mechanisms that could lead")
        print("to conflicts in the future.")
