# Documentation Plan

## Overview

This document outlines the documentation structure and content plan for SBoxMgr.

## Current Status

### ✅ Completed
- [x] Basic CLI documentation
- [x] Installation guide
- [x] Quick start guide
- [x] Configuration management
- [x] Subscription management
- [x] Troubleshooting guide
- [x] Security documentation
- [x] Architecture documentation

### 🔄 In Progress
- [x] TUI (Text User Interface) documentation
- [ ] i18n integration documentation
- [ ] Advanced usage examples

### 📋 Planned
- [ ] Plugin system documentation
- [ ] API reference
- [ ] Performance tuning guide
- [ ] Migration guides

## TUI Documentation Status

### ✅ Completed Features
- [x] Subscription management screen
- [x] Server list with exclusions
- [x] Configuration generation
- [x] Profile integration
- [x] Multi-subscription support (temporary)
- [x] Keyboard and mouse navigation
- [x] State persistence

### 📝 Documentation Updates Needed
- [ ] Add TUI section to main documentation
- [ ] Create TUI user guide
- [ ] Update quick start to include TUI
- [ ] Add TUI troubleshooting section
- [ ] Update CLI reference to mention TUI alternative

## Documentation Structure

### Core Documentation
```
docs/
├── README.md                    # Main documentation index
├── getting-started/            # Installation and first steps
│   ├── installation.md
│   ├── quick-start.md         # ⚠️ Needs TUI update
│   └── configuration.md
├── user-guide/                # User-facing documentation
│   ├── cli-reference.md       # ⚠️ Needs TUI mention
│   ├── tui-guide.md           # 🆕 NEW: TUI documentation
│   ├── configs.md
│   ├── subscriptions.md
│   └── troubleshooting.md     # ⚠️ Needs TUI section
├── developer/                 # Developer documentation
├── internal/                  # Internal architecture
├── reference/                 # API and schema reference
└── security.md               # Security considerations
```

## TUI Documentation Plan

### New Files to Create
1. **`docs/user-guide/tui-guide.md`** - Complete TUI user guide
2. **`docs/user-guide/tui-troubleshooting.md`** - TUI-specific troubleshooting
3. **`docs/internal/tui-architecture.md`** - TUI technical architecture

### Files to Update
1. **`docs/README.md`** - Add TUI to documentation structure
2. **`docs/getting-started/quick-start.md`** - Add TUI as alternative to CLI
3. **`docs/user-guide/cli-reference.md`** - Mention TUI as alternative interface
4. **`docs/user-guide/troubleshooting.md`** - Add TUI troubleshooting section

## Content Plan

### TUI User Guide (`tui-guide.md`)
- Overview and benefits
- Getting started with TUI
- Screen-by-screen guide
- Keyboard shortcuts
- Configuration management
- Subscription management
- Server exclusions
- Profile system integration
- Tips and best practices

### TUI Troubleshooting (`tui-troubleshooting.md`)
- Common TUI issues
- Debug mode usage
- Log analysis
- Performance issues
- State persistence problems
- Navigation issues

### Quick Start Update
- Add TUI as primary interface option
- Show both CLI and TUI approaches
- Emphasize TUI for new users
- Keep CLI for advanced users

## Implementation Priority

### High Priority
1. Create TUI user guide
2. Update quick start guide
3. Add TUI to main documentation index

### Medium Priority
1. Create TUI troubleshooting guide
2. Update CLI reference
3. Add TUI architecture documentation

### Low Priority
1. Create video tutorials
2. Add screenshots
3. Create interactive examples

## Quality Standards

- All documentation must be available in English and Russian
- Include practical examples
- Provide troubleshooting sections
- Keep documentation up-to-date with code changes
- Use consistent formatting and structure
- Include version information

## Review Process

1. Technical review by developers
2. User experience review
3. Translation review
4. Final approval and publication

## Maintenance

- Update documentation with each release
- Review and update quarterly
- Collect user feedback for improvements
- Monitor documentation usage analytics

---

**Last updated**: 2025-01-05
**Next review**: 2025-02-05
