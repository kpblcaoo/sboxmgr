# sboxmgr — Subbox Configuration Manager

[![Build Status](https://github.com/kpblcaoo/sboxmgr/actions/workflows/ci-dev.yml/badge.svg)](https://github.com/kpblcaoo/sboxmgr/actions)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/kpblcaoo/sboxmgr/actions)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-green.svg)](LICENSE)

A Python CLI tool for managing configuration files. Part of the subbox ecosystem for configuration management and generation.

**Note**: This tool is designed for configuration management purposes. Users are responsible for ensuring compliance with local laws and regulations.

## 🚀 Quick Start

### 1. Install
```bash
# Install from TestPyPI
pip install -i https://test.pypi.org/simple sboxmgr

# Or install in development mode
git clone https://github.com/kpblcaoo/sboxmgr.git
cd sboxmgr
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

For IPC functionality (agent communication), you also need to install sbox-common:

```bash
# Clone sbox-common repository
git clone https://github.com/kpblcaoo/sbox-common.git
cd sbox-common
pip install -e .

# Or install with optional dependencies
pip install sboxmgr[ipc]
```

### 2. Create configuration profile
Create a profile file with your configuration preferences:

```bash
# Example profile.json
{
  "export": {
    "format": "json",
    "output": "./config.json"
  }
}
```

### 3. Generate configuration
```bash
# Export configuration using profile
sboxmgr export -p profile.json

# Or use command line options
sboxmgr export --format json --output config.json
```

That's it! Your configuration file is ready.

## ✨ Key Features

- **Simple CLI**: One command to generate configuration files
- **Multiple formats**: JSON, YAML, and other configuration formats
- **Profile-based**: Use configuration profiles for consistent settings
- **Plugin system**: Extensible architecture with custom plugins
- **Flexible input**: Supports various input formats and sources
- **Production ready**: Comprehensive error handling and validation

## 📖 Common Usage

### Basic Operations
```bash
# Export configuration using profile
sboxmgr export -p profile.json

# Export with command line options
sboxmgr export --format json --output config.json

# Preview configuration without saving (dry-run)
sboxmgr export -p profile.json --dry-run

# List available configuration options
sboxmgr list --help
```

### Profile Management
```bash
# Create a new profile
sboxmgr profile create my-profile

# List available profiles
sboxmgr profile list

# Export using specific profile
sboxmgr export --profile my-profile
```

### Advanced Configuration
```bash
# Use custom configuration format
sboxmgr export --format yaml --output config.yaml

# Set custom output directory
sboxmgr export -p profile.json --output-dir ./configs/

# Validate configuration before export
sboxmgr export -p profile.json --validate
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Config file location (default: ./config.json)
SBOXMGR_CONFIG_FILE=./config.json

# Log file location
SBOXMGR_LOG_FILE=./sboxmgr.log

# Profile directory
SBOXMGR_PROFILE_DIR=./profiles/

# Language (en, ru, de, zh, etc.)
SBOXMGR_LANG=en
```

### Default Behavior
- **Config output**: `./config.json` (or `SBOXMGR_CONFIG_FILE`)
- **Logging**: `./sboxmgr.log` (or `SBOXMGR_LOG_FILE`)
- **Profiles**: `./profiles/` (or `SBOXMGR_PROFILE_DIR`)
- **Language**: English (or `SBOXMGR_LANG`)

## 🔧 Advanced Features

### Plugin System
Create custom plugins for data processing:

```bash
# Generate plugin template
sboxmgr plugin-template fetcher MyCustomFetcher --output-dir ./plugins/

# Use custom plugin
sboxmgr export --fetcher my-custom-fetcher
```

### Policy Engine
Configure processing policies:

```bash
# List available policies
sboxmgr policy list

# Apply custom policy
sboxmgr export --policy my-policy
```

### Internationalization
```bash
# Set language
sboxmgr lang --set ru

# View available languages
sboxmgr lang
```

## 🛠 Development

### Setup Development Environment
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run linting
ruff check src/

# Format code
black src/
```

### Project Structure
```
src/sboxmgr/
├── cli/          # Command-line interface
├── core/         # Core business logic
├── config/       # Configuration management
├── export/       # Configuration export
├── models/       # Data models
├── i18n/         # Internationalization
└── utils/        # Utilities
```

## 📚 Documentation

- [User Guide](docs/user-guide/) - Detailed usage instructions
- [CLI Reference](docs/user-guide/cli-reference.md) - Complete command reference
- [Configuration Guide](docs/getting-started/configuration.md) - Advanced configuration
- [Security](docs/security.md) - Security considerations
- [Development](docs/developer/) - Contributing guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CONTRIBUTING.md](docs/developer/contributing.md) for detailed guidelines.

## 📄 License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [subbox](https://github.com/kpblcaoo/subbox) - Configuration management ecosystem
- [sbox-common](https://github.com/kpblcaoo/sbox-common) - Common utilities

## 📚 Legacy

This project supersedes the earlier `update-singbox` script. While some internal components originated from it, `sboxmgr` is a full rewrite and represents a new generation of flexible, extensible configuration generation tools.

## Author

Mikhail Stepanov (<kpblcaoo@gmail.com>), [github.com/kpblcaoo](https://github.com/kpblcaoo)

---

**Need help?** Check the [troubleshooting guide](docs/user-guide/troubleshooting.md) or open an issue on GitHub.
