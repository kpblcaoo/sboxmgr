# Installation

This guide covers installing SBoxMgr on different platforms.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for development installation)

## Installation Methods

### From PyPI (Recommended)

```bash
pip install sboxmgr
```

### From Source

```bash
# Clone repository
git clone https://github.com/your-repo/sboxmgr.git
cd sboxmgr

# Install in development mode
pip install -e .
```

### Using pipx (Isolated Environment)

```bash
# Install pipx if not available
python -m pip install --user pipx

# Install SBoxMgr
pipx install sboxmgr
```

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install SBoxMgr
pip3 install sboxmgr
```

#### CentOS/RHEL/Fedora
```bash
# Install Python and pip
sudo dnf install python3 python3-pip

# Install SBoxMgr
pip3 install sboxmgr
```

#### Arch Linux
```bash
# Install from AUR
yay -S sboxmgr

# Or install manually
pip install sboxmgr
```

### macOS

#### Using Homebrew
```bash
# Install Homebrew if not available
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install SBoxMgr
brew install sboxmgr
```

#### Using pip
```bash
# Install Python (if not available)
brew install python

# Install SBoxMgr
pip3 install sboxmgr
```

### Windows

#### Using pip
```cmd
# Install Python from python.org
# Then install SBoxMgr
pip install sboxmgr
```

#### Using Chocolatey
```cmd
# Install Chocolatey if not available
# Then install SBoxMgr
choco install sboxmgr
```

## Verification

After installation, verify that SBoxMgr is working:

```bash
# Check version
sboxctl --version

# Show help
sboxctl --help

# Test basic functionality
sboxctl config generate --output test.json
```

## Configuration

### Initial Setup

1. Create configuration directory:
```bash
mkdir -p ~/.config/sboxmgr
```

2. Generate initial configuration:
```bash
sboxctl config generate --output ~/.config/sboxmgr/config.json
```

3. Set environment variables:
```bash
# Add to ~/.bashrc or ~/.zshrc
export SBOXMGR_CONFIG_FILE="$HOME/.config/sboxmgr/config.json"
export SBOXMGR_LOG_FILE="$HOME/.config/sboxmgr/sboxmgr.log"
```

### Configuration File

The default configuration file location is:
- Linux/macOS: `~/.config/sboxmgr/config.json`
- Windows: `%APPDATA%\sboxmgr\config.json`

Example configuration:
```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "output_path": "/etc/sing-box/config.json"
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/sboxmgr.log"
  }
}
```

## Dependencies

SBoxMgr automatically installs required dependencies:

- `pydantic` - Data validation
- `typer` - CLI framework
- `httpx` - HTTP client
- `pyyaml` - YAML support
- `rich` - Terminal output

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Install for current user only
pip install --user sboxmgr

# Or use virtual environment
python -m venv sboxmgr-env
source sboxmgr-env/bin/activate
pip install sboxmgr
```

#### Python Version Issues
```bash
# Check Python version
python3 --version

# Use specific Python version
python3.9 -m pip install sboxmgr
```

#### Network Issues
```bash
# Use alternative package index
pip install -i https://pypi.org/simple/ sboxmgr

# Install with trusted host
pip install --trusted-host pypi.org sboxmgr
```

### Uninstallation

```bash
# Remove SBoxMgr
pip uninstall sboxmgr

# Remove configuration files
rm -rf ~/.config/sboxmgr
```

## Next Steps

After installation:

1. [Quick Start](quick-start.md) - Get started with SBoxMgr
2. [Configuration](configuration.md) - Configure SBoxMgr
3. [CLI Reference](../user-guide/cli-reference.md) - Learn about commands

## See Also

- [Quick Start](quick-start.md) - First steps
- [Configuration](configuration.md) - System setup
- [Troubleshooting](../user-guide/troubleshooting.md) - Problem solving 