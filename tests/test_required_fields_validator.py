"""Tests for RequiredFieldsValidator with enhanced identifier validation."""

import pytest
from unittest.mock import Mock
from sboxmgr.subscription.validators.required_fields import RequiredFieldsValidator
from sboxmgr.subscription.models import PipelineContext


class MockServer:
    """Mock server for testing."""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_validator_accepts_valid_server():
    """Test that validator accepts server with all required fields."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="default")
    
    server = MockServer(
        type="vmess",
        port=443,
        address="example.com"
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    assert len(result.errors) == 0


def test_validator_accepts_server_with_tag():
    """Test that validator accepts server with tag as identifier."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="default")
    
    server = MockServer(
        type="vmess",
        port=443,
        tag="valid-tag"
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    assert len(result.errors) == 0


def test_validator_accepts_server_with_name():
    """Test that validator accepts server with meta.name as identifier."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="default")
    
    server = MockServer(
        type="vmess",
        port=443,
        meta={"name": "server-name"}
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    assert len(result.errors) == 0


def test_validator_rejects_invalid_tag():
    """Test that validator rejects server with invalid tag format."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="default")
    
    server = MockServer(
        type="vmess",
        port=443,
        tag="invalid tag with spaces"
    )
    
    result = validator.validate([server], context)
    
    assert not result.valid
    assert len(result.valid_servers) == 0
    assert len(result.errors) == 1
    assert "invalid tag format" in result.errors[0]


def test_validator_rejects_missing_identifier():
    """Test that validator rejects server without any identifier."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="default")
    
    server = MockServer(
        type="vmess",
        port=443
    )
    
    result = validator.validate([server], context)
    
    assert not result.valid
    assert len(result.valid_servers) == 0
    assert len(result.errors) == 1
    assert "missing identifier" in result.errors[0]


def test_validator_fixes_missing_identifier_in_tolerant_mode():
    """Test that validator fixes missing identifier in tolerant mode."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="tolerant")
    
    server = MockServer(
        type="vmess",
        port=443
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    assert len(result.errors) == 1  # Still logs the error
    
    # Check that address was generated
    assert hasattr(server, 'address')
    assert server.address.startswith("vmess-server-")
    
    # Check that fixes were logged
    fixes = context.metadata.get("validation_fixes", [])
    assert len(fixes) == 1
    assert fixes[0]['fix_type'] == 'generated_address'
    assert fixes[0]['severity'] == 'warning'


def test_validator_uses_tag_as_address():
    """Test that validator uses tag as address when address is missing."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="tolerant")
    
    server = MockServer(
        type="vmess",
        port=443,
        tag="my-server"
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    
    # Check that tag was used as address
    assert server.address == "my-server"
    
    # Check that fix was logged
    fixes = context.metadata.get("validation_fixes", [])
    assert len(fixes) == 1
    assert fixes[0]['fix_type'] == 'tag_to_address'
    assert fixes[0]['severity'] == 'info'


def test_validator_uses_name_as_address():
    """Test that validator uses meta.name as address when address is missing."""
    validator = RequiredFieldsValidator()
    context = PipelineContext(mode="tolerant")
    
    server = MockServer(
        type="vmess",
        port=443,
        meta={"name": "my-server-name"}
    )
    
    result = validator.validate([server], context)
    
    assert result.valid
    assert len(result.valid_servers) == 1
    
    # Check that name was used as address
    assert server.address == "my-server-name"
    
    # Check that fix was logged
    fixes = context.metadata.get("validation_fixes", [])
    assert len(fixes) == 1
    assert fixes[0]['fix_type'] == 'name_to_address'
    assert fixes[0]['severity'] == 'info'


def test_get_server_identifier():
    """Test the _get_server_identifier method."""
    validator = RequiredFieldsValidator()
    
    # Test with address
    server = MockServer(address="example.com")
    assert validator._get_server_identifier(server) == "example.com"
    
    # Test with tag (when no address)
    server = MockServer(tag="my-tag")
    assert validator._get_server_identifier(server) == "my-tag"
    
    # Test with name (when no address or tag)
    server = MockServer(meta={"name": "my-name"})
    assert validator._get_server_identifier(server) == "my-name"
    
    # Test fallback
    server = MockServer()
    identifier = validator._get_server_identifier(server)
    assert identifier.startswith("server-")
