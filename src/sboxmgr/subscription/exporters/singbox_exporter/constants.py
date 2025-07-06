"""Constants for sing-box exporter."""

# Supported protocol types
SUPPORTED_PROTOCOLS = {
    "vless", "vmess", "trojan", "ss", "shadowsocks",
    "wireguard", "hysteria2", "tuic", "shadowtls",
    "anytls", "tor", "ssh"
}

# Protocol normalization mapping
PROTOCOL_NORMALIZATION = {
    "ss": "shadowsocks"
}

# Configuration whitelisted fields
CONFIG_WHITELIST = {
    "password", "method", "multiplex", "packet_encoding",
    "udp_over_tcp", "udp_relay_mode", "udp_fragment", "udp_timeout"
}

# Default URLTest configuration
DEFAULT_URLTEST_CONFIG = {
    "url": "https://www.gstatic.com/generate_204",
    "interval": "3m",
    "tolerance": 50,
    "idle_timeout": "30m",
    "interrupt_exist_connections": False
}

# Transport types
TRANSPORT_TYPES = ("ws", "grpc", "tcp", "udp")

# TLS configuration fields
TLS_CONFIG_FIELDS = {
    "tls", "sni", "alpn", "server_name", "insecure", "utls"
}
