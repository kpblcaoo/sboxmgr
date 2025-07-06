# JSON Schemas

This directory contains JSON schemas generated from Pydantic models for SBoxMgr configuration validation.

## 📋 Generated Schemas

### Core Configuration
- **`sboxmgr-config.schema.json`** - Main application configuration
- **`logging-config.schema.json`** - Logging configuration
- **`service-config.schema.json`** - Service configuration
- **`app-settings.schema.json`** - Application settings

### Profile Schemas (ADR-0017)
- **`full-profile.schema.json`** - Complete profile configuration
- **`subscription-profile.schema.json`** - Subscription settings
- **`filter-profile.schema.json`** - Filtering configuration
- **`routing-profile.schema.json`** - Routing settings
- **`export-profile.schema.json`** - Export configuration
- **`agent-profile.schema.json`** - Agent settings
- **`ui-profile.schema.json`** - UI preferences
- **`legacy-profile.schema.json`** - Legacy profile support

### Client and Inbound
- **`client-profile.schema.json`** - Client configuration
- **`inbound-profile.schema.json`** - Inbound settings

### Sing-box Configuration
- **`singbox-config.schema.json`** - Complete sing-box configuration schema (199KB)

## 🔄 Generation

All schemas are automatically generated from Pydantic models using:

```bash
python scripts/generate_schemas.py
```

This implements **ADR-0016: Pydantic as Single Source of Truth** for validation and schema generation.

## 📊 Schema Statistics

- **Total schemas**: 15
- **Generated from**: Pydantic models
- **Schema version**: Draft-07
- **Generator**: sboxmgr-schema-generator v1.0.0

## 🎯 Usage

### Validation
```python
import json
from jsonschema import validate

# Load schema
with open('schemas/singbox-config.schema.json') as f:
    schema = json.load(f)

# Validate configuration
validate(instance=config, schema=schema)
```

### IDE Support
- Use schemas for autocompletion in editors
- Enable JSON schema validation in VS Code
- Reference schemas in documentation

### CI/CD Integration
- Validate configurations against schemas
- Generate documentation from schemas
- Ensure schema consistency

## 📈 Maintenance

- **Auto-generated**: Do not edit schemas manually
- **Source of truth**: Pydantic models in `src/sboxmgr/`
- **Updates**: Run generation script after model changes
- **Versioning**: Schemas include version metadata

## 🔗 Related

- [ADR-0016: Pydantic Schema Generation](../docs/arch/decisions/ADR-0016-pydantic-schema-generation.md)
- [Pydantic Models](../src/sboxmgr/models/)
- [Schema Generator](../scripts/generate_schemas.py)

---

**Last Updated**: 2025-01-05
**Generated**: 15 schemas from Pydantic models
