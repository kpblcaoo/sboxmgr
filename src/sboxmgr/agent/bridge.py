"""Agent bridge implementation for sboxmgr <-> sboxagent communication.

This module implements the AgentBridge class that handles communication with
external sboxagent processes through JSON API calls.
"""

import json
import subprocess
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

from .protocol import (
    ValidationRequest, InstallRequest, CheckRequest,
    ValidationResponse, InstallResponse, CheckResponse,
    ClientType, AgentCommand, AnyRequest, AnyResponse
)


def _get_logger():
    """Get logger lazily to avoid initialization issues."""
    from ..logging import get_logger
    return get_logger(__name__)


def _get_trace_id():
    """Get trace ID lazily to avoid initialization issues."""
    from ..logging.trace import get_trace_id
    return get_trace_id()


class AgentError(Exception):
    """Base exception for agent communication errors."""
    pass


class AgentNotAvailableError(AgentError):
    """Raised when sboxagent is not available or not found."""
    pass


class AgentBridge:
    """Bridge for communicating with external sboxagent.
    
    This class handles all communication with sboxagent processes, including
    validation, installation, and status checking. It follows the JSON API
    contract defined in protocol.py.
    
    Args:
        agent_path: Path to sboxagent executable (auto-detected if None)
        timeout: Timeout for agent operations in seconds
        
    Example:
        >>> bridge = AgentBridge()
        >>> if bridge.is_available():
        ...     result = bridge.validate("/path/to/config.json")
        ...     print(f"Valid: {result.success}")
    """
    
    def __init__(self, agent_path: Optional[str] = None, timeout: int = 30):
        """Initialize the agent bridge.
        
        Args:
            agent_path: Path to sboxagent executable
            timeout: Timeout for operations in seconds
        """
        self.agent_path = agent_path or self._find_agent()
        self.timeout = timeout
        self._available = None  # Cache availability check
    
    def _find_agent(self) -> Optional[str]:
        """Find sboxagent executable in PATH.
        
        Returns:
            Path to sboxagent executable or None if not found
        """
        return shutil.which("sbox-agent") or shutil.which("sboxagent")
    
    def is_available(self) -> bool:
        """Check if sboxagent is available.
        
        Returns:
            True if sboxagent is available and responsive
        """
        if self._available is not None:
            return self._available
        
        if not self.agent_path:
            self._available = False
            return False
        
        try:
            # Quick version check to verify agent is working
            request = {"command": "version", "version": "1.0"}
            response = self._call_agent(request)
            self._available = response.get("success", False)
            return self._available
        except Exception as e:
            _get_logger().debug(f"Agent availability check failed: {e}")
            self._available = False
            return False
    
    def validate(self, config_path: Path, client_type: Optional[ClientType] = None, 
                strict: bool = True) -> ValidationResponse:
        """Validate configuration file using sboxagent.
        
        Args:
            config_path: Path to configuration file
            client_type: Optional client type hint
            strict: Whether to perform strict validation
            
        Returns:
            ValidationResponse with validation results
            
        Raises:
            AgentNotAvailableError: If sboxagent is not available
            AgentError: If validation fails due to agent error
            
        Example:
            >>> bridge = AgentBridge()
            >>> response = bridge.validate(Path("config.json"))
            >>> if not response.success:
            ...     print(f"Errors: {response.errors}")
        """
        if not self.is_available():
            raise AgentNotAvailableError("sboxagent is not available")
        
        request = ValidationRequest(
            config_path=str(config_path),
            client_type=client_type,
            strict=strict,
            trace_id=_get_trace_id()
        )
        
        try:
            response_data = self._call_agent(request.model_dump())
            return ValidationResponse(**response_data)
        except Exception as e:
            _get_logger().error(f"Agent validation failed: {e}", extra={"trace_id": _get_trace_id()})
            raise AgentError(f"Validation failed: {e}") from e
    
    def install(self, client_type: ClientType, version: Optional[str] = None,
               force: bool = False) -> InstallResponse:
        """Install VPN client using sboxagent.
        
        Args:
            client_type: Type of client to install
            version: Optional specific version
            force: Whether to force reinstall
            
        Returns:
            InstallResponse with installation results
            
        Raises:
            AgentNotAvailableError: If sboxagent is not available
            AgentError: If installation fails
        """
        if not self.is_available():
            raise AgentNotAvailableError("sboxagent is not available")
        
        request = InstallRequest(
            client_type=client_type,
            version=version,
            force=force,
            trace_id=_get_trace_id()
        )
        
        try:
            response_data = self._call_agent(request.model_dump())
            return InstallResponse(**response_data)
        except Exception as e:
            _get_logger().error(f"Agent installation failed: {e}", extra={"trace_id": _get_trace_id()})
            raise AgentError(f"Installation failed: {e}") from e
    
    def check(self, client_type: Optional[ClientType] = None) -> CheckResponse:
        """Check client availability using sboxagent.
        
        Args:
            client_type: Optional specific client to check
            
        Returns:
            CheckResponse with client status
            
        Raises:
            AgentNotAvailableError: If sboxagent is not available
            AgentError: If check fails
        """
        if not self.is_available():
            raise AgentNotAvailableError("sboxagent is not available")
        
        request = CheckRequest(
            client_type=client_type,
            trace_id=_get_trace_id()
        )
        
        try:
            response_data = self._call_agent(request.model_dump())
            return CheckResponse(**response_data)
        except Exception as e:
            _get_logger().error(f"Agent check failed: {e}", extra={"trace_id": _get_trace_id()})
            raise AgentError(f"Check failed: {e}") from e
    
    def _call_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call sboxagent with JSON request.
        
        Args:
            request: JSON request dictionary
            
        Returns:
            JSON response dictionary
            
        Raises:
            AgentError: If agent call fails
        """
        if not self.agent_path:
            raise AgentError("Agent path not set")
        
        try:
            # Convert request to JSON
            request_json = json.dumps(request)
            
            # Call agent with JSON input
            result = subprocess.run(
                [self.agent_path, "--json"],
                input=request_json,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False  # Don't raise on non-zero exit
            )
            
            # Log stderr for debugging (technical logs)
            if result.stderr:
                _get_logger().debug(f"Agent stderr: {result.stderr}")
            
            # Parse JSON response from stdout
            if not result.stdout.strip():
                raise AgentError(f"Empty response from agent (exit code: {result.returncode})")
            
            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise AgentError(f"Invalid JSON response: {e}") from e
            
            # Check for agent-level errors
            if result.returncode != 0 and not response.get("success"):
                error_msg = response.get("message", f"Agent failed with exit code {result.returncode}")
                raise AgentError(error_msg)
            
            return response
            
        except subprocess.TimeoutExpired as e:
            raise AgentError(f"Agent timeout after {self.timeout}s") from e
        except subprocess.SubprocessError as e:
            raise AgentError(f"Agent subprocess error: {e}") from e
        except Exception as e:
            raise AgentError(f"Unexpected agent error: {e}") from e 