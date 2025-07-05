# Contributing to SBoxMgr

Welcome to SBoxMgr! This guide will help you get started with contributing to the project.

## Quick Start

### Prerequisites
- Python 3.8+
- Git
- Basic knowledge of Python and CLI development

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kpblcaoo/update-singbox.git
   cd update-singbox
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install .[dev]
   ```

4. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **Run tests to verify setup:**
   ```bash
   pytest
   ```

## Development Workflow

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code. Release tags (`v1.4.0`, `v1.5.0` …). |
| `develop` | Integration branch for next version. |
| `release/x.y.z` | Pre-release stabilization. |
| `hotfix/x.y.z+1` | Critical fixes for `main`. |

### Creating Feature Branches

```bash
git checkout develop && git pull
git checkout -b feat/feature-name
```

### Commit Guidelines

Use conventional commit messages:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```bash
git commit -m "feat: add support for WireGuard protocol"
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes
3. Add tests for new functionality
4. Update documentation if needed
5. Run tests: `pytest`
6. Create a Pull Request to `develop`
7. Request review from maintainers

## Code Standards

### Python Style

- Follow PEP 8 style guidelines
- Use type hints for all public functions
- Write docstrings in Google style format
- Keep functions small and focused

### Testing

- Write tests for all new functionality
- Aim for >90% code coverage
- Include edge case tests
- Use descriptive test names

Example test:
```python
def test_parse_vless_uri_valid():
    """Test parsing valid VLESS URI."""
    uri = "vless://uuid@server:port?security=tls#name"
    result = parse_uri(uri)
    assert result.protocol == "vless"
    assert result.uuid == "uuid"
```

### Documentation

- Update relevant documentation
- Add examples for new features
- Include troubleshooting information
- Keep documentation in sync with code

## Plugin Development

### Plugin Architecture

SBoxMgr uses a plugin-based architecture for extensibility:

- **Fetchers**: Download subscription data
- **Parsers**: Parse different subscription formats
- **Exporters**: Export to different formats
- **Validators**: Validate server configurations
- **Postprocessors**: Process server lists

### Creating a New Plugin

1. **Generate plugin template:**
   ```bash
   sboxctl plugin-template fetcher MyCustomFetcher
   ```

2. **Implement the plugin:**
   ```python
   from sboxmgr.subscription.fetchers.base_fetcher import BaseFetcher
   from sboxmgr.subscription.models import SubscriptionData
   
   class MyCustomFetcher(BaseFetcher):
       """Custom fetcher for special subscription format."""
       
       def fetch(self, url: str, **kwargs) -> SubscriptionData:
           """Fetch subscription data from custom source."""
           # Implementation here
           pass
   ```

3. **Register the plugin:**
   ```python
   from sboxmgr.subscription.registry import register
   
   @register("my_custom")
   class MyCustomFetcher(BaseFetcher):
       # Implementation
       pass
   ```

4. **Add tests:**
   ```python
   def test_my_custom_fetcher():
       """Test custom fetcher functionality."""
       fetcher = MyCustomFetcher()
       result = fetcher.fetch("test://example.com")
       assert result.servers
   ```

### Plugin Best Practices

- **Fail-safe**: Handle errors gracefully
- **Stateless**: Don't store state between calls
- **Configurable**: Accept configuration parameters
- **Testable**: Write comprehensive tests
- **Documented**: Include clear docstrings

## Middleware Development

### Middleware Pattern

Middleware processes server lists between parsing and export:

```python
from sboxmgr.subscription.middleware.base import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    """Custom middleware for server processing."""
    
    def process(self, servers: List[ParsedServer], context: Context) -> List[ParsedServer]:
        """Process server list."""
        # Implementation here
        return processed_servers
```

### Middleware Best Practices

- **Order matters**: Middleware is applied in sequence
- **Error handling**: Accumulate errors in context
- **Performance**: Keep processing efficient
- **Logging**: Use appropriate log levels

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── edge/          # Edge case tests
└── e2e/           # End-to-end tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_parser.py

# Run with coverage
pytest --cov=sboxmgr --cov-report=html

# Run edge case tests
pytest tests/edge/
```

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **Edge case tests**: Test error conditions
- **End-to-end tests**: Test complete workflows

## CI/CD

### Automated Checks

- **Linting**: Code style and quality
- **Testing**: Unit and integration tests
- **Coverage**: Code coverage reporting
- **Documentation**: Documentation validation

### Local Pre-commit

Install pre-commit hooks:
```bash
pre-commit install
```

## Getting Help

### Resources

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions
- **Code**: Review existing code for examples

### Asking Questions

When asking for help:
- Describe what you're trying to do
- Include error messages
- Show relevant code
- Mention your environment

## Release Process

### Versioning

SBoxMgr follows semantic versioning:
- **Major**: Breaking changes
- **Minor**: New features
- **Patch**: Bug fixes

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create release tag
6. Deploy to PyPI

## Code of Conduct

- Be respectful and inclusive
- Help others learn
- Follow project guidelines
- Report issues constructively

## License

By contributing to SBoxMgr, you agree that your contributions will be licensed under the MIT License.

---

For more detailed information, see the [internal development documentation](../internal/development/contributing.md). 