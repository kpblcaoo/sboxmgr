# Development

This directory contains development guides, best practices, and internal development documentation.

## 📋 Documents

- [Contributing Guide](contributing.md) - How to contribute to SBoxMgr
- [Testing Guide](testing.md) - Testing procedures and best practices
- [Test Plan](testplan.md) - Testing strategy and test cases
- [Edge Cases](edge-cases.md) - Edge case testing scenarios
- [Architect Role](architect-role.md) - Architecture role responsibilities
- [LLM Integration](llm-integration.md) - Large Language Model integration
- [Internationalization](i18n.md) - Multi-language support
- [Development Workflow](workflow.md) - Development process and procedures

## 🎯 Purpose

Development documents ensure:
- **Consistent practices** - Standardized development approach
- **Quality assurance** - Testing and review procedures
- **Team collaboration** - How to work together effectively
- **Code quality** - Best practices and standards

## 🛠️ Development Environment

### Prerequisites
- Python 3.8+
- Virtual environment
- Development dependencies

### Setup
```bash
git clone <repository>
cd sboxmgr
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Testing
```bash
pytest tests/
pytest --cov=src/sboxmgr
```

## 📈 Maintenance

- Update with new practices
- Review quarterly
- Keep examples current
- Document new tools

---

**Last Updated:** 2025-01-05
