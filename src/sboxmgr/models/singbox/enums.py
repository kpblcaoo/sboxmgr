"""Enums for sing-box configuration."""

from enum import Enum


class LogLevel(str, Enum):
    """Log level for sing-box."""

    trace = "trace"
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"
    panic = "panic"


class DomainStrategy(str, Enum):
    """Domain resolution strategy."""

    prefer_ipv4 = "prefer_ipv4"
    prefer_ipv6 = "prefer_ipv6"
    ipv4_only = "ipv4_only"
    ipv6_only = "ipv6_only"


class Network(str, Enum):
    """Network type for connections."""

    tcp = "tcp"
    udp = "udp"
    tcp_udp = "tcp,udp"
    
    @classmethod
    def from_string(cls, value: str) -> "Network":
        """Convert string to Network enum, handling legacy formats."""
        if value == "tcp_udp":
            return cls.tcp_udp
        return cls(value) 