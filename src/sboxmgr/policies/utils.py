"""Utility functions for policy system."""

from typing import Any, Optional


def extract_metadata_field(
    obj: Any, field_name: str, fallback_fields: Optional[list] = None
) -> Optional[Any]:
    """Extract field value from object with fallback options.

    Tries to extract a field from an object using multiple strategies:
    1. Direct field access (obj.field_name)
    2. Dictionary access (obj.get(field_name))
    3. Metadata access (obj.meta.get(field_name))
    4. Fallback fields (obj.get(fallback_field))

    Args:
        obj: Object to extract field from
        field_name: Primary field name to look for
        fallback_fields: Additional field names to try if primary not found

    Returns:
        Field value or None if not found

    """
    if not obj:
        return None

    # Try direct attribute access
    if hasattr(obj, field_name):
        value = getattr(obj, field_name)
        if value is not None:
            return value

    # Try dictionary access (only if object has get method)
    if hasattr(obj, "get") and callable(obj.get):
        value = obj.get(field_name)
        if value is not None:
            return value

        # Try metadata (only if object has get method)
        metadata = obj.get("meta", {})
        if isinstance(metadata, dict):
            value = metadata.get(field_name)
            if value is not None:
                return value

    # Try metadata access for Pydantic models
    if hasattr(obj, "meta") and isinstance(obj.meta, dict):
        value = obj.meta.get(field_name)
        if value is not None:
            return value

    # Try fallback fields
    if fallback_fields:
        for fallback_field in fallback_fields:
            if hasattr(obj, fallback_field):
                value = getattr(obj, fallback_field)
                if value is not None:
                    return value

            if hasattr(obj, "get") and callable(obj.get):
                value = obj.get(fallback_field)
                if value is not None:
                    return value

            # Try fallback fields in metadata for Pydantic models
            if hasattr(obj, "meta") and isinstance(obj.meta, dict):
                value = obj.meta.get(fallback_field)
                if value is not None:
                    return value

    return None


def validate_mode(mode: str, allowed_modes: list) -> bool:
    """Validate mode parameter.

    Args:
        mode: Mode to validate
        allowed_modes: List of allowed modes

    Returns:
        True if mode is valid

    Raises:
        ValueError: If mode is not in allowed_modes

    """
    if mode not in allowed_modes:
        raise ValueError(f"Mode '{mode}' not allowed. Must be one of: {allowed_modes}")
    return True
