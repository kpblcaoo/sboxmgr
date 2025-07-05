# Testing

This guide covers testing practices and guidelines for SBoxMgr development.

## Overview

SBoxMgr uses a comprehensive testing strategy with multiple layers of testing to ensure code quality and reliability.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for workflows
├── edge/             # Edge case and error condition tests
├── e2e/              # End-to-end workflow tests
└── conftest.py       # Shared test fixtures
```

## Test Types

### Unit Tests
Test individual functions and classes in isolation.

**Location:** `tests/unit/`

**Examples:**
- Parser functionality
- Model validation
- Utility functions
- CLI command logic

**Running unit tests:**
```bash
# Run all unit tests
pytest tests/unit/

# Run specific unit test file
pytest tests/unit/test_parsers.py

# Run with coverage
pytest tests/unit/ --cov=sboxmgr
```

### Integration Tests
Test component interactions and workflows.

**Location:** `tests/integration/`

**Examples:**
- Full subscription pipeline
- CLI command integration
- Profile management
- Export workflows

**Running integration tests:**
```bash
# Run integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_full_workflow.py
```

### Edge Case Tests
Test error conditions and edge cases.

**Location:** `tests/edge/`

**Examples:**
- Malformed input handling
- Network error recovery
- Invalid configuration handling
- Resource exhaustion

**Running edge tests:**
```bash
# Run edge case tests
pytest tests/edge/

# Run specific edge test
pytest tests/edge/test_parser_edge_cases.py
```

### End-to-End Tests
Test complete user workflows.

**Location:** `tests/e2e/`

**Examples:**
- Complete CLI workflows
- Real subscription processing
- Configuration generation

**Running e2e tests:**
```bash
# Run e2e tests
pytest tests/e2e/

# Run with real data
pytest tests/e2e/ --real-data
```

## Test Configuration

### Environment Setup
Tests use isolated environments to prevent interference:

```python
# conftest.py
import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup isolated test environment."""
    # Set test-specific environment variables
    os.environ['SBOXMGR_CONFIG_FILE'] = './test_config.json'
    os.environ['SBOXMGR_LOG_FILE'] = './test_sboxmgr.log'
    os.environ['SBOXMGR_EXCLUSION_FILE'] = './test_exclusions.json'
    os.environ['SBOXMGR_DEBUG'] = '0'
    
    yield
    
    # Cleanup test files
    for file in ['test_config.json', 'test_sboxmgr.log', 'test_exclusions.json']:
        if os.path.exists(file):
            os.remove(file)
```

### Test Data
Use dedicated test data to ensure consistent results:

```python
# tests/data/
├── singbox_configs/    # Sample sing-box configurations
├── subscriptions/      # Sample subscription data
└── profiles/          # Sample profile files
```

## Writing Tests

### Test Naming Convention
```python
def test_function_name_with_description():
    """Test description."""
    # Test implementation
    pass

def test_class_name_method_name():
    """Test specific method behavior."""
    # Test implementation
    pass
```

### Test Structure
```python
def test_parser_handles_valid_input():
    """Test that parser correctly handles valid input."""
    # Arrange
    input_data = "valid subscription data"
    parser = ClashParser()
    
    # Act
    result = parser.parse(input_data)
    
    # Assert
    assert len(result) > 0
    assert all(isinstance(server, ParsedServer) for server in result)
```

### Mocking External Dependencies
```python
import pytest
from unittest.mock import patch, Mock

def test_fetcher_handles_network_errors():
    """Test fetcher handles network errors gracefully."""
    with patch('requests.get') as mock_get:
        # Arrange
        mock_get.side_effect = requests.RequestException("Network error")
        fetcher = URLFetcher()
        
        # Act & Assert
        with pytest.raises(FetchError):
            fetcher.fetch("https://example.com/subscription")
```

### CLI Testing
Use Typer's test client for CLI testing:

```python
from typer.testing import CliRunner
from sboxmgr.cli.main import app

def test_list_servers_command():
    """Test list-servers command."""
    runner = CliRunner()
    
    # Test with valid URL
    result = runner.invoke(app, ["list-servers", "-u", "https://example.com/sub"])
    assert result.exit_code == 0
    
    # Test with invalid URL
    result = runner.invoke(app, ["list-servers", "-u", "invalid-url"])
    assert result.exit_code != 0
```

## Test Coverage

### Coverage Requirements
- Minimum 90% code coverage
- 100% coverage for critical paths
- Edge case coverage for error handling

### Running Coverage
```bash
# Run tests with coverage
pytest --cov=sboxmgr --cov-report=html

# Generate coverage report
coverage report

# View HTML coverage report
open htmlcov/index.html
```

### Coverage Exclusions
```ini
# .coveragerc
[run]
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    setup.py
```

## Performance Testing

### Load Testing
Test performance with large datasets:

```python
def test_parser_performance_large_dataset():
    """Test parser performance with large dataset."""
    # Generate large test dataset
    large_data = generate_large_subscription_data(1000)
    
    # Measure parsing time
    start_time = time.time()
    parser = ClashParser()
    result = parser.parse(large_data)
    end_time = time.time()
    
    # Assert performance requirements
    assert end_time - start_time < 5.0  # Should complete within 5 seconds
    assert len(result) == 1000
```

### Memory Testing
Monitor memory usage during tests:

```python
import psutil
import os

def test_memory_usage():
    """Test memory usage during processing."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    process_large_dataset()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assert memory usage is reasonable
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
```

## Continuous Integration

### GitHub Actions
Tests run automatically on every commit:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=sboxmgr --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
Run tests before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Debugging Tests

### Verbose Output
```bash
# Run tests with verbose output
pytest -v

# Run with maximum verbosity
pytest -vvv

# Show print statements
pytest -s
```

### Debugging Specific Tests
```bash
# Run specific test with debugger
pytest tests/unit/test_parser.py::test_specific_function -s

# Run with pdb
pytest --pdb

# Run with ipdb (if installed)
pytest --pdbcls=IPython.terminal.debugger:Pdb
```

### Test Isolation
```bash
# Run tests in isolation
pytest --dist=no

# Run single test file
pytest tests/unit/test_specific.py

# Run specific test function
pytest tests/unit/test_specific.py::test_function_name
```

## Best Practices

### Test Organization
1. **Group related tests** in test classes
2. **Use descriptive test names** that explain the scenario
3. **Keep tests independent** - no shared state between tests
4. **Use fixtures** for common setup and teardown

### Test Data Management
1. **Use dedicated test data** - don't rely on external services
2. **Mock external dependencies** - network calls, file system
3. **Clean up after tests** - remove temporary files and data
4. **Use realistic test data** - representative of real usage

### Error Testing
1. **Test error conditions** - invalid input, network failures
2. **Test edge cases** - empty data, malformed input
3. **Test recovery** - how system handles and recovers from errors
4. **Test error messages** - ensure they're helpful and accurate

### Performance Testing
1. **Test with realistic data sizes** - not just small examples
2. **Monitor resource usage** - memory, CPU, network
3. **Set performance baselines** - know what's acceptable
4. **Test scalability** - how system performs under load

## See Also

- [Contributing](contributing.md) - Development guidelines
- [Architecture](architecture.md) - System architecture
- [Security](../security.md) - Security testing considerations
