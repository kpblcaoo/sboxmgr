"""Protocol common enums for VPN protocols validation.

This module provides common enumeration types used across different VPN protocols
for consistent validation and configuration handling.
"""

from enum import Enum


class LogLevel(str, Enum):
    """Logging levels for clients."""

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