# Documentation Update Plan

## Overview

This document outlines the plan for updating SBoxMgr documentation to reflect the current state of the project and follow best practices.

## ✅ Completed Updates

### Core Documentation
- [x] **README.md** - Completely rewritten with simple 3-step quick start
- [x] **docs/README.md** - Updated structure and removed broken links
- [x] **docs/getting-started/installation.md** - Updated for source installation
- [x] **docs/getting-started/quick-start.md** - Converted to English, updated commands
- [x] **docs/getting-started/configuration.md** - Updated for environment variables
- [x] **docs/user-guide/cli-reference.md** - Updated with actual commands
- [x] **docs/user-guide/profiles.md** - Updated profile system documentation
- [x] **docs/user-guide/subscriptions.md** - Updated subscription management
- [x] **docs/developer/architecture.md** - Converted to English, updated structure
- [x] **docs/developer/testing.md** - Updated testing practices

### Documentation Structure
- [x] **Internal documentation reorganization** - Moved all internal docs to `docs/internal/`
- [x] **Category organization** - Created 6 categories with README files
- [x] **File renaming** - Standardized naming conventions

### Schema Documentation
- [x] **Schema cleanup** - Removed outdated schema files
- [x] **Pydantic schema generation** - Updated generator script
- [x] **Sing-box schema** - Added complete sing-box configuration schema
- [x] **Schema documentation** - Created comprehensive README
- [x] **15 schemas generated** - All from Pydantic models

### Russian Documentation Alignment ✅ COMPLETED
- [x] **docs/ru/README.md** - Completely rewrite to match English version
- [x] **docs/ru/SHOWCASE.md** - Update to match current CLI commands
- [x] **docs/ru/CHANGELOG.md** - Sync with English changelog
- [x] **docs/ru/DEVELOPMENT.md** - Update development guide
- [x] **docs/ru/cli_reference.md** - Update CLI reference
- [x] **docs/ru/guides/profile_management.md** - Update profile management guide
- [x] **docs/ru/tests/edge_cases.md** - Update edge cases documentation

## 🔄 In Progress

### Documentation Structure
- [x] **docs/user-guide/troubleshooting.md** - Update with actual error scenarios ✅ COMPLETED
- [x] **docs/developer/contributing.md** - Update development workflow ✅ COMPLETED
- [x] **docs/security.md** - Review and update security documentation ✅ COMPLETED

## 📋 Remaining Tasks

### User Documentation
- [ ] **docs/user-guide/profiles.md** - Add more practical examples
- [x] **docs/user-guide/troubleshooting.md** - Add common error solutions ✅ COMPLETED
- [ ] **docs/getting-started/configuration.md** - Add more environment variables

### Developer Documentation
- [x] **docs/developer/contributing.md** - Update contribution guidelines ✅ COMPLETED
- [ ] **docs/developer/api-reference.md** - Create API documentation
- [ ] **docs/developer/plugins.md** - Create plugin development guide

### Reference Documentation
- [ ] **docs/reference/examples/** - Add more configuration examples
- [ ] **docs/CHANGELOG.md** - Review and update changelog format

### Internationalization ✅ COMPLETED
- [x] **docs/ru/README.md** - Update Russian documentation
- [x] **docs/ru/CHANGELOG.md** - Update Russian changelog
- [x] **docs/ru/DEVELOPMENT.md** - Update Russian development guide
- [x] **docs/ru/cli_security.md** - Update CLI security guide
- [x] **docs/ru/i18n.md** - Update internationalization guide

## 🎯 Quality Improvements

### Content Quality
- [ ] Remove outdated information
- [ ] Update all command examples
- [ ] Add more practical use cases
- [ ] Improve error messages and solutions

### Structure Quality
- [ ] Standardize document format
- [ ] Improve navigation between documents
- [ ] Add cross-references
- [ ] Create index pages

### Technical Quality
- [ ] Validate all code examples
- [ ] Test all command examples
- [ ] Update version numbers
- [ ] Fix broken links

## 📊 Documentation Standards

### Writing Style
- Use clear, concise language
- Provide practical examples
- Include troubleshooting sections
- Use consistent terminology

### Code Examples
- Test all code examples
- Use realistic data
- Include error handling
- Show complete workflows

### Structure
- Logical organization
- Clear headings and sections
- Consistent formatting
- Easy navigation

## 🔧 Tools and Automation

### Documentation Tools
- [ ] Set up automatic link checking
- [ ] Implement documentation testing
- [ ] Add spell checking
- [ ] Create documentation templates

### Quality Assurance
- [ ] Review process for new documentation
- [ ] Automated validation
- [ ] User feedback collection
- [ ] Regular documentation audits

## 📈 Metrics and Goals

### Success Metrics
- [ ] 100% command accuracy
- [ ] 0 broken links
- [ ] 90%+ user satisfaction
- [ ] Reduced support requests

### Documentation Goals
- [ ] Complete coverage of all features
- [ ] Clear migration paths
- [ ] Comprehensive troubleshooting
- [ ] Developer-friendly guides

## 🚀 Implementation Timeline

### Phase 1: Core Updates (Completed)
- ✅ Main README and structure
- ✅ Installation and quick start
- ✅ CLI reference and user guides
- ✅ Internal documentation reorganization

### Phase 2: Schema Documentation (Completed)
- ✅ Clean up outdated schema files
- ✅ Update Pydantic schema generator
- ✅ Add complete sing-box configuration schema
- ✅ Create comprehensive schema documentation

### Phase 3: Russian Documentation Alignment ✅ COMPLETED
- ✅ Update Russian README to match English
- ✅ Update Russian SHOWCASE and CLI reference
- ✅ Sync Russian changelog and development docs
- ✅ Ensure all Russian docs reflect current state

### Phase 4: Quality and Polish ✅ COMPLETED
- ✅ Link validation
- ✅ Content review
- ✅ User testing

## 📝 Maintenance Plan

### Regular Reviews
- Monthly documentation reviews
- Quarterly content updates
- Annual comprehensive audit

### Update Triggers
- New feature releases
- Breaking changes
- User feedback
- Bug reports

### Version Control
- Track documentation changes
- Maintain changelog
- Tag documentation versions
- Archive old versions

## 🤝 Community Involvement

### User Feedback
- Collect feedback on documentation
- Address common questions
- Improve based on usage patterns
- Regular user surveys

### Contributor Guidelines
- Clear contribution process
- Documentation templates
- Review guidelines
- Recognition for contributors

## 📚 Resources

### Documentation Tools
- Markdown editors
- Link checkers
- Spell checkers
- Documentation generators

### Best Practices
- Technical writing guidelines
- Open source documentation standards
- User experience principles
- Accessibility guidelines

## Отчет о проверке качества документации (2025-01-05)

### Найденные и исправленные ошибки CLI команд:

1. **clear-exclusions** - неправильная команда
   - **Было:** `sboxctl clear-exclusions --yes`
   - **Стало:** `sboxctl exclusions --clear --yes`
   - **Исправлено в:** CLI reference (EN/RU), README (RU), SHOWCASE (RU)

2. **config validate --file** - неправильный синтаксис
   - **Было:** `sboxctl config validate --file config.json`
   - **Стало:** `sboxctl config validate config.json`
   - **Исправлено в:** CLI reference (RU)

3. **config generate** - несуществующая команда
   - **Было:** `sboxctl config generate --output template.json`
   - **Стало:** `sboxctl config dump --format json` / `sboxctl config schema --output schema.json`
   - **Исправлено в:** CLI reference (EN/RU)

4. **profile validate --file** - неправильный синтаксис
   - **Было:** `sboxctl profile validate --file profile.json`
   - **Стало:** `sboxctl profile validate profile.json`
   - **Исправлено в:** CLI reference (EN/RU), profiles.md, profile_management.md, configuration.md

5. **profile apply --name** - неправильный синтаксис
   - **Было:** `sboxctl profile apply --name home`
   - **Стало:** `sboxctl profile apply profile.json`
   - **Исправлено в:** CLI reference (EN/RU), profiles.md, profile_management.md, troubleshooting.md

6. **profile switch --name** - неправильный синтаксис
   - **Было:** `sboxctl profile switch --name work`
   - **Стало:** `sboxctl profile switch work`
   - **Исправлено в:** CLI reference (EN/RU)

7. **policy evaluate** - несуществующая команда
   - **Было:** `sboxctl policy evaluate --config config.json`
   - **Стало:** `sboxctl policy test --profile profile.json`
   - **Исправлено в:** CLI reference (EN/RU)

8. **policy test --config** - неправильный синтаксис
   - **Было:** `sboxctl policy test --config config.json`
   - **Стало:** `sboxctl policy test --profile profile.json`
   - **Исправлено в:** CLI reference (EN/RU)

9. **policy audit --url** - неправильный синтаксис
   - **Было:** `sboxctl policy audit --url "https://example.com/proxy.json"`
   - **Стало:** `sboxctl policy audit --servers servers.json`
   - **Исправлено в:** CLI reference (EN/RU)

### Результат:
- ✅ Все CLI команды в документации теперь соответствуют реальному интерфейсу
- ✅ Синтаксис всех команд исправлен согласно help выводам
- ✅ Удалены несуществующие команды и заменены на правильные
- ✅ Документация полностью синхронизирована с актуальным CLI

### Статус: ЗАВЕРШЕНО ✅

---

**Last Updated:** 2025-07-05
**Status:** Phase 1, 2 & 3 Complete, Phase 4 (Quality and Polish) Completed
