"""Protocol-specific validator using Pydantic models.

This module provides protocol-specific validation using the detailed Pydantic models
from protocol_models.py. It ensures that server configurations meet the strict
requirements for each protocol type and generates proper error messages for
invalid configurations.

Implements ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation.
"""

from typing import Any

from sboxmgr.subscription.models import PipelineContext

from .base import BaseParsedValidator, ValidationResult, register_parsed_validator
from .protocol_models import generate_protocol_schema, validate_protocol_config


@register_parsed_validator("protocol_specific")
class ProtocolSpecificValidator(BaseParsedValidator):
    """Validates server configurations using protocol-specific Pydantic models.

    This validator uses the detailed protocol models to ensure that each server
    configuration meets the strict requirements for its protocol type. It validates
    encryption methods, port ranges, TLS settings, and other protocol-specific
    parameters.

    Features:
    - Protocol-specific validation using Pydantic models
    - Detailed error messages for invalid configurations
    - Support for all major protocols (Shadowsocks, VMess, VLESS, Trojan, WireGuard)
    - Automatic schema generation for documentation
    """

    def validate(self, servers: list, context: PipelineContext) -> ValidationResult:
        """Validate server configurations using protocol-specific models.

        Args:
            servers: List of ParsedServer objects to validate.
            context: Pipeline execution context.

        Returns:
            ValidationResult: Contains validation errors and list of valid servers.

        """
        errors = []
        valid_servers = []

        for idx, server in enumerate(servers):
            try:
                # Skip unknown servers (they're handled by other validators)
                if getattr(server, "type", None) == "unknown":
                    valid_servers.append(server)
                    continue

                # Convert ParsedServer to dict for validation
                server_dict = self._parsed_server_to_dict(server)

                # Validate using protocol-specific models
                validate_protocol_config(server_dict, server.type)

                # If validation passes, add to valid servers
                valid_servers.append(server)

            except Exception as e:
                error_msg = (
                    f"Server[{idx}] ({getattr(server, 'type', 'unknown')}): {str(e)}"
                )
                errors.append(error_msg)

                # In tolerant mode, still include the server but mark it as having errors
                if context.mode == "tolerant":
                    if not hasattr(server, "meta"):
                        server.meta = {}
                    server.meta["validation_errors"] = [str(e)]
                    valid_servers.append(server)

        return ValidationResult(
            valid=bool(valid_servers), errors=errors, valid_servers=valid_servers
        )

    def _parsed_server_to_dict(self, server) -> dict[str, Any]:
        """Convert ParsedServer to dictionary for protocol validation.

        Args:
            server: ParsedServer object to convert.

        Returns:
            Dictionary representation suitable for protocol validation.

        """
        server_dict = {
            "server": getattr(server, "address", ""),
            "server_port": getattr(server, "port", 0),
        }

        # Add protocol-specific fields
        if hasattr(server, "meta") and server.meta:
            server_dict.update(server.meta)

        # Add security field if present
        if hasattr(server, "security") and server.security:
            server_dict["method"] = server.security  # For Shadowsocks

        return server_dict


@register_parsed_validator("enhanced_required_fields")
class EnhancedRequiredFieldsValidator(BaseParsedValidator):
    """Enhanced required fields validator with protocol-specific checks.

    This validator extends the basic required fields validation with
    protocol-specific requirements and better error messages.
    """

    def validate(self, servers: list, context: PipelineContext) -> ValidationResult:
        """Validate required fields with protocol-specific enhancements.

        Args:
            servers: List of ParsedServer objects to validate.
            context: Pipeline execution context.

        Returns:
            ValidationResult: Contains validation errors and list of valid servers.

        """
        errors = []
        valid_servers = []

        for idx, server in enumerate(servers):
            server_errors = []

            # Basic required fields
            if not hasattr(server, "type") or not server.type:
                server_errors.append("missing type")
            elif not hasattr(server, "address") or not server.address:
                server_errors.append("missing address")
            elif (
                not hasattr(server, "port")
                or not isinstance(server.port, int)
                or not (1 <= server.port <= 65535)
            ):
                server_errors.append(f"invalid port: {getattr(server, 'port', None)}")

            # Protocol-specific required fields
            if hasattr(server, "type") and server.type:
                protocol_errors = self._validate_protocol_specific_fields(server)
                server_errors.extend(protocol_errors)

            if server_errors:
                errors.append(
                    f"Server[{idx}] ({getattr(server, 'type', 'unknown')}): {'; '.join(server_errors)}"
                )
                if context.mode == "tolerant":
                    # In tolerant mode, still include the server but mark errors
                    if not hasattr(server, "meta"):
                        server.meta = {}
                    server.meta["validation_errors"] = server_errors
                    valid_servers.append(server)
            else:
                valid_servers.append(server)

        return ValidationResult(
            valid=bool(valid_servers), errors=errors, valid_servers=valid_servers
        )

    def _validate_protocol_specific_fields(self, server) -> list[str]:
        """Validate protocol-specific required fields.

        Args:
            server: ParsedServer object to validate.

        Returns:
            List of validation error messages.

        """
        errors = []

        if server.type == "ss":
            # Shadowsocks requires method and password
            if not hasattr(server, "security") or not server.security:
                errors.append("missing encryption method")
            if (
                not hasattr(server, "meta")
                or not server.meta
                or "password" not in server.meta
            ):
                errors.append("missing password")

        elif server.type == "vmess":
            # VMess requires UUID
            if (
                not hasattr(server, "meta")
                or not server.meta
                or "uuid" not in server.meta
            ):
                errors.append("missing UUID")

        elif server.type == "vless":
            # VLESS requires UUID
            if (
                not hasattr(server, "meta")
                or not server.meta
                or "uuid" not in server.meta
            ):
                errors.append("missing UUID")

        elif server.type == "trojan":
            # Trojan requires password
            if (
                not hasattr(server, "meta")
                or not server.meta
                or "password" not in server.meta
            ):
                errors.append("missing password")

        return errors


def validate_single_protocol_config(
    config: dict[str, Any], protocol: str
) -> dict[str, Any]:
    """Validate a single protocol configuration.

    Args:
        config: Configuration dictionary to validate.
        protocol: Protocol type (shadowsocks, vmess, vless, trojan, wireguard).

    Returns:
        Validated configuration dictionary.

    Raises:
        ValueError: If configuration is invalid.

    """
    return validate_protocol_config(config, protocol)


def get_protocol_schema(protocol: str) -> dict[str, Any]:
    """Get JSON schema for a protocol configuration.

    Args:
        protocol: Protocol type.

    Returns:
        JSON schema dictionary.

    Raises:
        ValueError: If protocol is not supported.

    """
    return generate_protocol_schema(protocol)
