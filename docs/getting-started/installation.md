# Installation

This guide covers installing SBoxMgr from source.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git

## Installation from Source

### 1. Clone Repository
```bash
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### 4. Verify Installation
```bash
# Check version
sboxctl --version

# Show help
sboxctl --help

# Test basic functionality
sboxctl list-servers --help
```

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Follow installation steps above
```

#### CentOS/RHEL/Fedora
```bash
# Install system dependencies
sudo dnf install python3 python3-pip git

# Follow installation steps above
```

#### Arch Linux
```bash
# Install system dependencies
sudo pacman -S python python-pip git

# Follow installation steps above
```

### macOS

#### Using Homebrew
```bash
# Install Python (if not available)
brew install python

# Follow installation steps above
```

### Windows

#### Using pip
```cmd
# Install Python from python.org
# Then follow installation steps above
```

## Configuration

### Initial Setup

1. Create configuration directory:
```bash
mkdir -p ~/.config/sboxmgr
```

2. Set environment variables:
```bash
# Add to ~/.bashrc or ~/.zshrc
export SBOXMGR_CONFIG_FILE="$HOME/.config/sboxmgr/config.json"
export SBOXMGR_LOG_FILE="$HOME/.config/sboxmgr/sboxmgr.log"
export SBOXMGR_EXCLUSION_FILE="$HOME/.config/sboxmgr/exclusions.json"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SBOXMGR_CONFIG_FILE` | `./config.json` | Output configuration file path |
| `SBOXMGR_LOG_FILE` | `./sboxmgr.log` | Log file path |
| `SBOXMGR_EXCLUSION_FILE` | `./exclusions.json` | Server exclusions file |
| `SBOXMGR_LANG` | `en` | Interface language |

## Dependencies

SBoxMgr automatically installs required dependencies:

- `pydantic>=2.0` - Data validation
- `typer>=0.9.0` - CLI framework
- `requests>=2.28.0` - HTTP client
- `python-dotenv` - Environment variable management
- `packaging>=21.0` - Version handling

## Development Setup

For development work:

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

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Install for current user only
pip install --user -e .

# Or use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### Python Version Issues
```bash
# Check Python version
python3 --version

# Use specific Python version
python3.9 -m venv .venv
```

#### Missing Dependencies
```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip install -e . --force-reinstall
```

### Getting Help

- Check the [troubleshooting guide](../user-guide/troubleshooting.md)
- Open an issue on [GitHub](https://github.com/kpblcaoo/update-singbox/issues)
- Review the [main README](../../README.md) for quick start examples

## Next Steps

After installation:

1. [Quick Start](quick-start.md) - Get started with SBoxMgr
2. [Configuration](configuration.md) - Configure SBoxMgr
3. [CLI Reference](../user-guide/cli-reference.md) - Learn about commands

## See Also

- [Quick Start](quick-start.md) - First steps
- [Configuration](configuration.md) - System setup
- [Troubleshooting](../user-guide/troubleshooting.md) - Problem solving 