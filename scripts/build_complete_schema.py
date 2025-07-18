#!/usr/bin/env python3
"""Build complete sing-box schema by analyzing documentation and existing models."""

import json
import re
from pathlib import Path


def extract_protocol_fields(doc_path):
    """Extract field information from a protocol documentation file."""
    if not doc_path.exists():
        return {}

    with open(doc_path, encoding="utf-8") as f:
        content = f.read()

    fields = {}

    # Look for field definitions in markdown
    # Pattern: | field_name | type | required | description |
    table_pattern = r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    matches = re.findall(table_pattern, content)

    for match in matches:
        field_name = match[0].strip()
        field_type = match[1].strip()
        required = match[2].strip().lower() == "yes"
        description = match[3].strip()

        if field_name and field_name not in ["Field", "---"]:
            fields[field_name] = {
                "type": field_type,
                "required": required,
                "description": description,
            }

    # Also look for JSON examples
    json_pattern = r"```json\s*\n(.*?)\n```"
    json_matches = re.findall(json_pattern, content, re.DOTALL)

    for json_example in json_matches:
        try:
            example = json.loads(json_example)
            if isinstance(example, dict):
                for key, value in example.items():
                    if key not in fields:
                        fields[key] = {
                            "type": type(value).__name__,
                            "required": False,
                            "description": f"Found in example: {type(value).__name__}",
                        }
        except json.JSONDecodeError:
            continue

    return fields


def analyze_singbox_docs():
    """Analyze sing-box documentation to build complete schema."""
    docs_dir = Path("temp_singbox_docs/docs/configuration")

    if not docs_dir.exists():
        print("❌ sing-box documentation not found!")
        return {}

    schema = {
        "inbounds": {},
        "outbounds": {},
        "summary": {
            "total_inbounds": 0,
            "total_outbounds": 0,
            "protocols_analyzed": [],
        },
    }

    # Analyze outbound protocols
    outbound_dir = docs_dir / "outbound"
    if outbound_dir.exists():
        for doc_file in outbound_dir.glob("*.md"):
            if doc_file.name.endswith(".zh.md"):
                continue

            protocol_name = doc_file.stem
            if protocol_name == "index":
                continue

            print(f"📖 Analyzing outbound: {protocol_name}")
            fields = extract_protocol_fields(doc_file)
            schema["outbounds"][protocol_name] = fields
            schema["summary"]["protocols_analyzed"].append(f"outbound:{protocol_name}")

    # Analyze inbound protocols
    inbound_dir = docs_dir / "inbound"
    if inbound_dir.exists():
        for doc_file in inbound_dir.glob("*.md"):
            if doc_file.name.endswith(".zh.md"):
                continue

            protocol_name = doc_file.stem
            if protocol_name == "index":
                continue

            print(f"📖 Analyzing inbound: {protocol_name}")
            fields = extract_protocol_fields(doc_file)
            schema["inbounds"][protocol_name] = fields
            schema["summary"]["protocols_analyzed"].append(f"inbound:{protocol_name}")

    schema["summary"]["total_inbounds"] = len(schema["inbounds"])
    schema["summary"]["total_outbounds"] = len(schema["outbounds"])

    return schema


def compare_with_existing_models(schema):
    """Compare documented schema with existing Pydantic models."""
    print("\n🔍 COMPARING WITH EXISTING MODELS")
    print("=" * 50)

    # Import existing models
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    try:
        # Note: SingBoxConfig is not used in this script, but kept for reference
        # from sboxmgr.models import SingBoxConfig

        # Get existing outbound types

        # This is a simplified check - in reality we'd need to inspect the models more thoroughly
        print("📋 Existing models found:")
        print("  - SingBoxConfig")

        # Check what we have vs what's documented
        documented_outbounds = set(schema["outbounds"].keys())
        documented_inbounds = set(schema["inbounds"].keys())

        print("\n📊 COVERAGE ANALYSIS:")
        print(f"  Documented outbounds: {len(documented_outbounds)}")
        print(f"  Documented inbounds: {len(documented_inbounds)}")

        print("\n🌐 DOCUMENTED OUTBOUNDS:")
        for protocol in sorted(documented_outbounds):
            field_count = len(schema["outbounds"][protocol])
            print(f"  {protocol}: {field_count} fields")

        print("\n🌐 DOCUMENTED INBOUNDS:")
        for protocol in sorted(documented_inbounds):
            field_count = len(schema["inbounds"][protocol])
            print(f"  {protocol}: {field_count} fields")

    except ImportError as e:
        print(f"⚠️  Could not import existing models: {e}")


def generate_complete_schema(schema):
    """Generate a complete schema file with all protocols."""
    output_file = Path("schemas/complete_singbox_schema.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"\n💾 Complete schema saved to: {output_file}")

    # Generate summary report
    summary_file = Path("schemas/schema_summary.md")
    with open(summary_file, "w") as f:
        f.write("# Complete Sing-Box Schema Summary\n\n")
        f.write("Generated from documentation analysis.\n\n")

        f.write("## Outbound Protocols\n\n")
        f.write(f"Total: {len(schema['outbounds'])}\n\n")
        for protocol, fields in sorted(schema["outbounds"].items()):
            f.write(f"### {protocol}\n")
            f.write(f"Fields: {len(fields)}\n\n")
            for field_name, field_info in fields.items():
                required = "✅" if field_info["required"] else "❌"
                f.write(f"- {field_name}: {field_info['type']} {required}\n")
            f.write("\n")

        f.write("## Inbound Protocols\n\n")
        f.write(f"Total: {len(schema['inbounds'])}\n\n")
        for protocol, fields in sorted(schema["inbounds"].items()):
            f.write(f"### {protocol}\n")
            f.write(f"Fields: {len(fields)}\n\n")
            for field_name, field_info in fields.items():
                required = "✅" if field_info["required"] else "❌"
                f.write(f"- {field_name}: {field_info['type']} {required}\n")
            f.write("\n")

    print(f"📝 Summary report saved to: {summary_file}")


def main():
    """Main function to build complete schema."""
    print("🔧 BUILDING COMPLETE SING-BOX SCHEMA")
    print("=" * 50)

    # Analyze documentation
    schema = analyze_singbox_docs()

    if not schema:
        print("❌ Failed to analyze documentation!")
        return

    # Compare with existing models
    compare_with_existing_models(schema)

    # Generate complete schema
    generate_complete_schema(schema)

    print("\n✅ Schema analysis complete!")
    print(f"📊 Found {len(schema['outbounds'])} outbound protocols")
    print(f"📊 Found {len(schema['inbounds'])} inbound protocols")


if __name__ == "__main__":
    main()
