"""Agent bridge module for sboxmgr <-> sboxagent communication.

This module provides the interface for communicating with external sboxagent
(which may be implemented in Go, Ruby, or other languages) through a well-defined
JSON API contract.
"""

from .bridge import AgentBridge, AgentError, AgentNotAvailableError
from .protocol import (
    AgentCommand,
    AgentRequest,
    AgentResponse,
    ClientType,
    InstallRequest,
    ValidationRequest,
)

__all__ = [
    "AgentBridge",
    "AgentError",
    "AgentNotAvailableError",
    "AgentRequest",
    "AgentResponse",
    "ValidationRequest",
    "InstallRequest",
    "ClientType",
    "AgentCommand",
]
