"""Constants for export command validation and configuration."""

# Allowed postprocessor types
ALLOWED_POSTPROCESSORS = [
    'geo_filter',
    'tag_filter', 
    'latency_sort'
]

# Allowed middleware types
ALLOWED_MIDDLEWARE = [
    'logging',
    'enrichment'
]

# Valid final route values
VALID_FINAL_ROUTES = [
    'auto',
    'direct',
    'block',
    'proxy',
    'dns'
]

# Valid outbound types for exclusion
VALID_OUTBOUND_TYPES = [
    # Basic outbound types
    'direct',
    'block',
    'dns',
    'proxy',
    'urltest',
    'selector',
    # Supported protocol types
    'vmess',
    'vless',
    'trojan',
    'shadowsocks',
    'ss',
    'hysteria2',
    'wireguard',
    'tuic',
    'shadowtls',
    'anytls',
    'tor',
    'ssh',
    'http',
    'socks'
]

# Valid inbound types
VALID_INBOUND_TYPES = [
    'tun',
    'socks',
    'http',
    'tproxy'
]

# Valid TUN stack types
VALID_TUN_STACKS = [
    'system',
    'gvisor',
    'mixed'
]

# Valid DNS modes
VALID_DNS_MODES = [
    'system',
    'tunnel',
    'off'
]

# Output format types
VALID_OUTPUT_FORMATS = [
    'json',
    'toml',
    'auto'
]

# Export format types
VALID_EXPORT_FORMATS = [
    'singbox',
    'clash'
]

# Default values
DEFAULT_TUN_ADDRESS = "198.18.0.1/16"
DEFAULT_TUN_MTU = 1500
DEFAULT_TUN_STACK = "mixed"
DEFAULT_SOCKS_PORT = 1080
DEFAULT_SOCKS_LISTEN = "127.0.0.1"
DEFAULT_HTTP_PORT = 8080
DEFAULT_HTTP_LISTEN = "127.0.0.1"
DEFAULT_TPROXY_PORT = 7895
DEFAULT_TPROXY_LISTEN = "0.0.0.0"
DEFAULT_DNS_MODE = "system"
DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_EXPORT_FORMAT = "singbox"
DEFAULT_OUTPUT_FILE = "config.json" 