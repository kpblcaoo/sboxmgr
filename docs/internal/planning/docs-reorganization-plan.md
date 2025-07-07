# Internal Documentation Reorganization Plan

## 🎯 Goals

1. **Improve discoverability** - Make internal docs easier to find
2. **Reduce clutter** - Organize files logically
3. **Separate concerns** - Distinguish user vs developer vs internal docs
4. **Maintain quality** - Keep only relevant, up-to-date documentation

## 📁 Proposed Structure

```
docs/
├── user-guide/              # End-user documentation
├── developer/               # Developer documentation
├── reference/               # API and schema references
├── internal/                # Internal team documentation
│   ├── planning/            # Roadmaps, plans, technical debt
│   ├── architecture/        # System architecture docs
│   ├── security/            # Security audits and policies
│   ├── migration/           # Migration guides
│   ├── structure/           # Project structure and dependencies
│   ├── development/         # Development processes
│   └── monitoring/          # Performance and maintenance
└── archive/                 # Deprecated documentation
```

## 📋 File Migration Plan

### Phase 1: Create Directory Structure
```bash
mkdir -p docs/internal/{planning,architecture,security,migration,structure,development,monitoring}
```

### Phase 2: Move and Rename Files

#### Planning & Roadmap
- `DOCUMENTATION_PLAN.md` → `internal/planning/docs-roadmap.md`
- `TECHNICAL_DEBT.md` → `internal/planning/technical-debt.md`
- `SCENARIOS.md` → `internal/planning/scenarios.md`

#### Architecture
- `pipeline.md` → `internal/architecture/pipeline.md`
- `EVENT_SYSTEM_GUIDE.md` → `internal/architecture/event-system.md`
- `AGENT_BRIDGE_USAGE.md` → `internal/architecture/agent-system.md`

#### Security
- `SECURITY_AUDIT_CHECKLIST.md` → `internal/security/audit-checklist.md`
- `CUSTOM_POLICIES_GUIDE.md` → `internal/security/custom-policies.md`
- `sec_checklist.md` → `internal/security/security-checklist.md`

#### Migration
- `AGENT_MIGRATION_GUIDE.md` → `internal/migration/agent-migration.md`
- `CLI_INBOUND_PARAMETERS.md` → `internal/migration/cli-updates.md`

#### Structure
- `struct.json` → `internal/structure/project-layout.json`
- Create `internal/structure/dependencies.md`
- Create `internal/structure/schema.md`

### Phase 3: Update References
- Update all internal links
- Update navigation files
- Update README files

## 🎯 Best Practices Implementation

### 1. File Naming Convention
- Use kebab-case for filenames
- Include category prefix when helpful
- Use descriptive names

### 2. Content Organization
- Start with overview/README in each directory
- Group related documents together
- Use consistent formatting

### 3. Cross-References
- Link between related documents
- Use relative paths
- Maintain link integrity

### 4. Version Control
- Keep documentation in sync with code
- Tag documentation versions
- Archive outdated content

## 📊 Benefits

### For Developers
- **Easier navigation** - Logical file organization
- **Better discoverability** - Clear categorization
- **Reduced maintenance** - Structured approach

### For New Contributors
- **Clear onboarding** - Obvious where to find information
- **Reduced confusion** - Separated user vs internal docs
- **Faster ramp-up** - Better organized knowledge

### For Project Maintenance
- **Cleaner structure** - Less clutter in root docs
- **Better scalability** - Easy to add new categories
- **Improved quality** - Forced organization improves content

## 🚀 Implementation Steps

### Step 1: Create New Structure
```bash
# Create directories
mkdir -p docs/internal/{planning,architecture,security,migration,structure,development,monitoring}

# Create index files
touch docs/internal/README.md
touch docs/internal/planning/README.md
touch docs/internal/architecture/README.md
# ... etc
```

### Step 2: Move Files
```bash
# Move planning files
mv docs/DOCUMENTATION_PLAN.md docs/internal/planning/docs-roadmap.md
mv docs/TECHNICAL_DEBT.md docs/internal/planning/technical-debt.md
mv docs/SCENARIOS.md docs/internal/planning/scenarios.md

# Move architecture files
mv docs/pipeline.md docs/internal/architecture/pipeline.md
mv docs/EVENT_SYSTEM_GUIDE.md docs/internal/architecture/event-system.md
mv docs/AGENT_BRIDGE_USAGE.md docs/internal/architecture/agent-system.md

# Move security files
mv docs/SECURITY_AUDIT_CHECKLIST.md docs/internal/security/audit-checklist.md
mv docs/CUSTOM_POLICIES_GUIDE.md docs/internal/security/custom-policies.md
mv docs/sec_checklist.md docs/internal/security/security-checklist.md

# Move migration files
mv docs/AGENT_MIGRATION_GUIDE.md docs/internal/migration/agent-migration.md
mv docs/CLI_INBOUND_PARAMETERS.md docs/internal/migration/cli-updates.md

# Move structure files
mv docs/struct.json docs/internal/structure/project-layout.json
```

### Step 3: Update Links
- Search for all references to moved files
- Update internal links
- Update navigation files
- Test all links

### Step 4: Clean Up
- Remove empty directories
- Update main docs README
- Archive truly outdated content

## 📈 Success Metrics

### Quantitative
- Reduced number of files in docs root (target: <10)
- Improved file organization (target: 100% categorized)
- Faster document discovery (target: <3 clicks to find any doc)

### Qualitative
- Developer satisfaction with documentation structure
- Reduced time to find specific information
- Improved onboarding experience for new contributors

## 🔄 Maintenance Plan

### Regular Reviews
- Monthly: Check for new uncategorized docs
- Quarterly: Review and update organization
- Annually: Comprehensive structure review

### Quality Gates
- All new internal docs must go in appropriate category
- No files in docs root without justification
- All links must be valid and working

---

**Status:** Planning Phase
**Next Steps:** Implement directory structure and begin file migration
