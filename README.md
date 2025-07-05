# SBoxMgr - Sing-box Configuration Manager

[![Build Status](https://github.com/kpblcaoo/update-singbox/actions/workflows/ci-dev.yml/badge.svg)](https://github.com/kpblcaoo/update-singbox/actions)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/kpblcaoo/update-singbox/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python CLI tool for managing [sing-box](https://sing-box.sagernet.org/) proxy configurations. Automatically fetches server lists, applies exclusions, generates configs, and supports advanced routing.

## 🚀 Quick Start (3 steps)

### 1. Install
```bash
# Clone and install
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
```

### 2. Get your proxy URL
You need a URL that provides sing-box compatible configuration (Clash, sing-box JSON, etc.). Common sources:
- Your VPN provider's subscription link
- A Clash configuration URL
- A sing-box configuration file

### 3. Generate config
```bash
# List available servers
sboxctl list-servers -u "YOUR_PROXY_URL_HERE"

# Generate config for server #1
sboxctl export -u "YOUR_PROXY_URL_HERE" --index 1

# Start sing-box with the generated config
sing-box run -c config.json
```

That's it! Your sing-box is now running with the selected server.

## ✨ Key Features

- **Simple CLI**: One command to generate working sing-box configs
- **Multiple protocols**: VLESS, Shadowsocks, VMess, Trojan, TUIC, Hysteria2
- **Smart routing**: Direct routing for Russian domains, proxy for others
- **Server management**: List, select, and exclude servers
- **Flexible input**: Supports Clash, sing-box JSON, and other formats
- **Production ready**: 90%+ test coverage, comprehensive error handling

## 📖 Common Usage

### Basic Operations
```bash
# List all available servers
sboxctl list-servers -u "https://example.com/proxy.json"

# Generate config for specific server
sboxctl export -u "https://example.com/proxy.json" --index 2

# Generate config for server by name
sboxctl export -u "https://example.com/proxy.json" --remarks "Fast Server"

# Preview config without saving (dry-run)
sboxctl export -u "https://example.com/proxy.json" --index 1 --dry-run
```

### Server Management
```bash
# Add server to exclusions (won't be used)
sboxctl exclusions -u "https://example.com/proxy.json" --add 3

# Remove server from exclusions
sboxctl exclusions -u "https://example.com/proxy.json" --remove 3

# View current exclusions
sboxctl exclusions --view

# Clear all exclusions
sboxctl clear-exclusions
```

### Advanced Configuration
```bash
# Configure custom inbound (SOCKS proxy on port 1080)
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --inbound-types socks --socks-port 1080

# Set custom routing (all traffic through proxy)
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --final-route proxy

# Exclude specific outbound types
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --exclude-outbounds block,dns
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Config file location (default: ./config.json)
SBOXMGR_CONFIG_FILE=/etc/sing-box/config.json

# Log file location
SBOXMGR_LOG_FILE=./sboxmgr.log

# Exclusions file
SBOXMGR_EXCLUSION_FILE=./exclusions.json

# Language (en, ru, de, zh, etc.)
SBOXMGR_LANG=en
```

### Default Behavior
- **Config output**: `./config.json` (or `SBOXMGR_CONFIG_FILE`)
- **Logging**: `./sboxmgr.log` (or `SBOXMGR_LOG_FILE`)
- **Exclusions**: `./exclusions.json` (or `SBOXMGR_EXCLUSION_FILE`)
- **Language**: English (or `SBOXMGR_LANG`)

## 🔧 Advanced Features

### Plugin System
Create custom fetchers, parsers, and exporters:

```bash
# Generate plugin template
sboxctl plugin-template fetcher MyCustomFetcher --output-dir ./plugins/

# Use custom plugin
sboxctl export -u "custom://my-data" --fetcher my-custom-fetcher
```

### Policy Engine
Configure routing policies:

```bash
# List available policies
sboxctl policy list

# Apply geo-based policy
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --policy geo-direct
```

### Internationalization
```bash
# Set language
sboxctl lang --set ru

# View available languages
sboxctl lang
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
├── subscription/ # Subscription management
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [sing-box](https://sing-box.sagernet.org/) - Universal proxy platform
- [Clash](https://github.com/Dreamacro/clash) - Rule-based proxy
- [sing-box-common](https://github.com/kpblcaoo/sing-box-common) - Common utilities

---

**Need help?** Check the [troubleshooting guide](docs/user-guide/troubleshooting.md) or open an issue on GitHub.
