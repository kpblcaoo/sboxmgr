# Testing Instructions

## Installing dependencies
Before running tests, make sure all dependencies are installed:
```bash
python -m venv .venv
source .venv/bin/activate
pip install .[dev]
cp .env.example .env  # Edit as needed
```

## Running tests
To run all tests, use:
```bash
pytest
```

## Checking test coverage
To check code coverage, use:
```bash
pytest --cov=. --cov-report=term-missing
```

## Test structure
- Tests are located in the `tests/` folder.
- Each module has a corresponding test file, for example:
  - `config_fetch.py` -> `tests/test_config_fetch.py`
  - `protocol_validation.py` -> `tests/test_protocol_validation.py`.
