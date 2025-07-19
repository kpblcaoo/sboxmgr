# Git Hooks and Quality Checks

This document describes the git hooks and quality checks used in the SBoxMgr project.

## Overview

The project uses a two-tier approach to quality checks:

1. **Pre-commit hooks**: Fast checks for immediate feedback during development
2. **Pre-push hooks**: Comprehensive checks before code reaches the repository

## Pre-commit Hooks

Fast checks that run on every commit to provide immediate feedback.

### Quick Import Check

**Purpose**: Fast validation that critical modules can be imported without building a wheel package.

**Execution**:
- Runs only when critical files are changed (`src/`, `pyproject.toml`, `setup.py`, `MANIFEST.in`)
- Takes ~1-2 seconds
- Tests direct imports of critical modules

**Critical modules tested**:
- `sboxmgr.cli.main`
- `sboxmgr.configs.models`
- `sboxmgr.configs.manager`
- `sboxmgr.export.export_manager`
- `sboxmgr.subscription.manager.core`
- `sboxmgr.core.orchestrator`
- `logsetup.setup`

**Benefits**:
- Catches import errors immediately
- Fast execution
- Conditional execution (only when needed)

### Other Pre-commit Checks

- **Ruff**: Linting and formatting
- **Detect-secrets**: Security scanning
- **I18N**: Internationalization key validation
- **Basic cleanup**: Whitespace, file endings, etc.

## Pre-push Hooks

Comprehensive checks that run before pushing to the repository.

### Full Wheel Integrity Check

**Purpose**: Complete validation of the wheel package in an isolated environment.

**Execution**:
- Runs on every push
- Takes ~10-30 seconds
- Creates temporary virtual environment
- Builds wheel package
- Tests all imports in isolated environment

**Benefits**:
- Catches packaging issues
- Validates wheel integrity
- Tests in clean environment
- Ensures code is ready for distribution

## Configuration

### Pre-commit Configuration

Located in `.pre-commit-config.yaml`:

```yaml
# Quick import check (fast alternative to wheel check)
- repo: local
  hooks:
    - id: quick-import-check
      name: Quick Import Check
      entry: python .hooks/quick_import_check.py
      language: system
      pass_filenames: false
      always_run: true
      # Only run if critical files changed
      files: ^(src/|pyproject\.toml|setup\.py|MANIFEST\.in)$
```

### Pre-push Configuration

Located in `.git/hooks/pre-push`:

```bash
#!/bin/bash
# Pre-push hook for SBoxMgr
# Performs full wheel integrity check before pushing to repository

# Run the full wheel integrity check
if python .hooks/check_build_contents.py; then
    echo "✅ Wheel integrity check passed"
else
    echo "❌ Wheel integrity check failed"
    exit 1
fi
```

## Scripts

### Quick Import Check

**File**: `.hooks/quick_import_check.py`

**Purpose**: Fast import validation without building wheel package.

**Usage**:
```bash
python .hooks/quick_import_check.py
```

### Full Wheel Check

**File**: `.hooks/check_build_contents.py`

**Purpose**: Complete wheel package validation.

**Usage**:
```bash
python .hooks/check_build_contents.py
```

## Workflow

### Development Workflow

1. **Make changes** to code
2. **Commit changes** - pre-commit hooks run automatically
   - Quick import check validates critical imports
   - Other quality checks run
3. **Push changes** - pre-push hooks run automatically
   - Full wheel integrity check validates packaging

### Troubleshooting

#### Quick Import Check Fails

```bash
# Run quick check manually
python .hooks/quick_import_check.py

# Fix import issues and try again
git add .
git commit -m "Fix import issues"
```

#### Full Wheel Check Fails

```bash
# Run full check manually
python .hooks/check_build_contents.py

# Fix packaging issues and try again
git push
```

#### Skip Pre-push Check (Emergency)

```bash
# Skip pre-push hooks (use with caution)
git push --no-verify
```

## Benefits of This Approach

### Speed
- Fast commits with quick checks
- Comprehensive validation only when needed

### Quality
- Immediate feedback on import issues
- Complete validation before repository push

### Developer Experience
- Reduced waiting time during development
- Clear error messages and guidance
- Conditional execution reduces unnecessary work

### Reliability
- Two-tier validation ensures quality
- Isolated testing environment
- Comprehensive coverage of critical paths

## Future Improvements

### Potential Enhancements

1. **Caching**: Cache wheel build results for unchanged files
2. **Parallel execution**: Run independent checks in parallel
3. **Incremental builds**: Only rebuild changed components
4. **Remote validation**: Run heavy checks on CI/CD instead of locally

### Monitoring

Track hook performance and effectiveness:
- Execution time metrics
- Failure rate analysis
- Developer feedback collection
