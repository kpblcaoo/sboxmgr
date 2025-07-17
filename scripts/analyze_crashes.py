#!/usr/bin/env python3
"""
Analyze collected crashes from fuzz testing to identify patterns and issues.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def analyze_crashes():
    """Analyze all crash files and categorize issues."""
    crashes_dir = Path("crashes")

    if not crashes_dir.exists():
        print("❌ No crashes directory found!")
        return

    crash_files = list(crashes_dir.glob("*.json"))
    if not crash_files:
        print("❌ No crash files found!")
        return

    print(f"🔍 Analyzing {len(crash_files)} crash files...")

    # Categories for analysis
    error_patterns = defaultdict(list)
    protocol_issues = defaultdict(list)
    field_issues = defaultdict(list)
    config_patterns = []

    for crash_file in crash_files:
        try:
            with open(crash_file) as f:
                crash_data = json.load(f)

            # Extract error message
            stderr = crash_data.get("stderr", "")
            error = crash_data.get("error", "")
            config = crash_data.get("config", {})

            # Categorize by error type
            if "duplicate" in stderr.lower():
                error_patterns["duplicate_tags"].append(
                    {"file": crash_file.name, "error": stderr, "config": config}
                )
            elif "unknown field" in stderr.lower():
                error_patterns["unknown_fields"].append(
                    {"file": crash_file.name, "error": stderr, "config": config}
                )
            elif "required" in stderr.lower():
                error_patterns["missing_required"].append(
                    {"file": crash_file.name, "error": stderr, "config": config}
                )
            elif "invalid" in stderr.lower():
                error_patterns["invalid_values"].append(
                    {"file": crash_file.name, "error": stderr, "config": config}
                )
            else:
                error_patterns["other"].append(
                    {"file": crash_file.name, "error": stderr, "config": config}
                )

            # Analyze by protocol
            if "outbounds" in config:
                for outbound in config["outbounds"]:
                    if isinstance(outbound, dict) and "type" in outbound:
                        protocol = outbound["type"]
                        protocol_issues[protocol].append(
                            {
                                "file": crash_file.name,
                                "error": stderr,
                                "outbound": outbound,
                            }
                        )

            # Analyze field issues
            if "unknown field" in stderr:
                # Extract field name from error
                match = re.search(r'unknown field "([^"]+)"', stderr)
                if match:
                    field_name = match.group(1)
                    field_issues[field_name].append(
                        {"file": crash_file.name, "error": stderr, "config": config}
                    )

            # Collect config patterns
            config_patterns.append(
                {
                    "file": crash_file.name,
                    "inbounds_count": len(config.get("inbounds", [])),
                    "outbounds_count": len(config.get("outbounds", [])),
                    "outbound_types": [
                        o.get("type")
                        for o in config.get("outbounds", [])
                        if isinstance(o, dict)
                    ],
                    "inbound_types": [
                        i.get("type")
                        for i in config.get("inbounds", [])
                        if isinstance(i, dict)
                    ],
                }
            )

        except Exception as e:
            print(f"⚠️  Error reading {crash_file}: {e}")

    # Print analysis results
    print("\n📊 CRASH ANALYSIS RESULTS")
    print("=" * 50)

    print("\n🔴 ERROR CATEGORIES:")
    for category, crashes in error_patterns.items():
        print(f"  {category}: {len(crashes)} crashes")
        if crashes:
            # Show first example
            example = crashes[0]
            print(f"    Example: {example['error'][:100]}...")

    print("\n🌐 PROTOCOL ISSUES:")
    for protocol, crashes in protocol_issues.items():
        print(f"  {protocol}: {len(crashes)} crashes")
        if crashes:
            # Show unique errors for this protocol
            errors = set()
            for crash in crashes:
                error_msg = crash["error"]
                if "unknown field" in error_msg:
                    match = re.search(r'unknown field "([^"]+)"', error_msg)
                    if match:
                        errors.add(f"unknown field: {match.group(1)}")
                elif "duplicate" in error_msg:
                    errors.add("duplicate tags")
                else:
                    errors.add(error_msg[:50] + "...")

            for error in list(errors)[:3]:  # Show first 3 unique errors
                print(f"    - {error}")

    print("\n📝 FIELD ISSUES:")
    for field, crashes in field_issues.items():
        print(f"  {field}: {len(crashes)} crashes")
        if crashes:
            # Show which protocols have this field
            protocols = set()
            for crash in crashes:
                if "outbounds" in crash["config"]:
                    for outbound in crash["config"]["outbounds"]:
                        if isinstance(outbound, dict) and "type" in outbound:
                            protocols.add(outbound["type"])
            print(f"    Found in protocols: {', '.join(protocols)}")

    print("\n📋 CONFIG PATTERNS:")
    total_configs = len(config_patterns)
    outbound_type_counts = Counter()
    inbound_type_counts = Counter()

    for pattern in config_patterns:
        outbound_type_counts.update(pattern["outbound_types"])
        inbound_type_counts.update(pattern["inbound_types"])

    print(f"  Total configs analyzed: {total_configs}")
    print(f"  Most common outbound types: {dict(outbound_type_counts.most_common(5))}")
    print(f"  Most common inbound types: {dict(inbound_type_counts.most_common(5))}")

    # Save detailed analysis
    analysis_file = crashes_dir / "analysis_report.json"
    with open(analysis_file, "w") as f:
        json.dump(
            {
                "summary": {
                    "total_crashes": len(crash_files),
                    "error_categories": {k: len(v) for k, v in error_patterns.items()},
                    "protocol_issues": {k: len(v) for k, v in protocol_issues.items()},
                    "field_issues": {k: len(v) for k, v in field_issues.items()},
                },
                "detailed_errors": dict(error_patterns),
                "protocol_issues": dict(protocol_issues),
                "field_issues": dict(field_issues),
                "config_patterns": config_patterns,
            },
            f,
            indent=2,
        )

    print(f"\n💾 Detailed analysis saved to: {analysis_file}")

    return {
        "error_patterns": error_patterns,
        "protocol_issues": protocol_issues,
        "field_issues": field_issues,
        "config_patterns": config_patterns,
    }


if __name__ == "__main__":
    analyze_crashes()
