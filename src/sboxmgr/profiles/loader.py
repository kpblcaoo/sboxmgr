"""Profile loading and validation utilities.

This module provides the ProfileLoader class for loading profiles from files
and validating their structure.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod

from pydantic import ValidationError

from ..profiles.models import FullProfile
from ..logging.core import get_logger

logger = get_logger(__name__)


class ProfileSectionValidator(ABC):
    """Interface for profile section validators."""

    @abstractmethod
    def validate(self, section_data: dict) -> list:
        """Validate profile section data.
        
        Args:
            section_data: Section data to validate.
            
        Returns:
            List of validation errors.
            
        """
        pass

class SubscriptionSectionValidator(ProfileSectionValidator):
    """Validator for subscription section of profiles."""
    
    def validate(self, section_data: dict) -> list:
        """Validate subscription section data.
        
        Args:
            section_data: Subscription section data to validate.
            
        Returns:
            List of validation error messages.
            
        """
        errors = []
        if not isinstance(section_data, list):
            errors.append("Subscriptions must be a list")
        else:
            for i, subscription in enumerate(section_data):
                if not isinstance(subscription, dict):
                    errors.append(f"Subscription {i} must be a dictionary")
                else:
                    if 'id' not in subscription:
                        errors.append(f"Subscription {i} must have 'id' field")
                    if 'priority' in subscription and not isinstance(subscription['priority'], int):
                        errors.append(f"Subscription {i} priority must be an integer")
        return errors

class ExportSectionValidator(ProfileSectionValidator):
    """Validator for export section of profiles."""
    
    def validate(self, section_data: dict) -> list:
        """Validate export section data.
        
        Args:
            section_data: Export section data to validate.
            
        Returns:
            List of validation error messages.
            
        """
        errors = []
        if 'format' in section_data:
            if section_data['format'] not in ['sing-box', 'clash', 'json']:
                errors.append("Export format must be 'sing-box', 'clash', or 'json'")
        if 'output_file' in section_data:
            if not isinstance(section_data['output_file'], str):
                errors.append("Export output_file must be a string")
        return errors

class FilterSectionValidator(ProfileSectionValidator):
    """Validator for filter section of profiles."""
    
    def validate(self, section_data: dict) -> list:
        """Validate filter section data.
        
        Args:
            section_data: Filter section data to validate.
            
        Returns:
            List of validation error messages.
            
        """
        errors = []
        for key in ('exclude_tags', 'only_tags', 'exclusions'):
            if key in section_data and not isinstance(section_data[key], list):
                errors.append(f"Filter {key} must be a list")
        if 'only_enabled' in section_data and not isinstance(section_data['only_enabled'], bool):
            errors.append("Filter only_enabled must be a boolean")
        return errors

# В реальном проекте можно сделать динамическую регистрацию
SECTION_VALIDATORS = {
    'subscriptions': SubscriptionSectionValidator(),
    'export': ExportSectionValidator(),
    'filters': FilterSectionValidator(),
}

class ProfileLoader:
    """Loader for profile files with validation and error handling.
    
    This class provides methods for loading profiles from various file formats
    (JSON, YAML) and validating their structure before creating FullProfile objects.
    
    Attributes:
        supported_formats: List of supported file formats

    """
    
    def __init__(self):
        """Initialize the ProfileLoader."""
        self.supported_formats = ['.json', '.yaml', '.yml']
        logger.debug("ProfileLoader initialized")
    
    def load_from_file(self, file_path: str) -> FullProfile:
        """Load a profile from file.
        
        Args:
            file_path: Path to the profile file
            
        Returns:
            FullProfile: Loaded profile
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
            ValidationError: If profile data is invalid

        """
        path = Path(file_path).expanduser().resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {file_path}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {path.suffix}. Supported: {self.supported_formats}")
        
        try:
            # Load data based on file format
            if path.suffix.lower() == '.json':
                profile_data = self._load_json(path)
            else:  # yaml/yml
                profile_data = self._load_yaml(path)
            
            # Validate structure
            validation_result = self.validate_structure(profile_data)
            if not validation_result['valid']:
                raise ValueError(f"Profile structure validation failed: {validation_result['errors']}")
            
            # Load profile using Pydantic
            try:
                profile = FullProfile(**profile_data)
                return profile
            except ValidationError as e:
                raise ValueError(f"Profile validation failed: {e}")
            except Exception as e:
                raise ValueError(f"Failed to load profile: {e}")
            
        except Exception as e:
            logger.error(f"Failed to load profile from {file_path}: {e}")
            raise
    
    def load_from_json(self, json_data: str) -> FullProfile:
        """Load a profile from JSON string.
        
        Args:
            json_data: JSON string containing profile data
            
        Returns:
            FullProfile: Loaded profile
            
        Raises:
            ValidationError: If JSON is invalid or profile data is invalid

        """
        try:
            profile_data = json.loads(json_data)
            
            # Validate structure
            validation_result = self.validate_structure(profile_data)
            if not validation_result['valid']:
                raise ValueError(f"Profile structure validation failed: {validation_result['errors']}")
            
            # Create profile
            profile = FullProfile(**profile_data)
            
            logger.info("Successfully loaded profile from JSON string")
            return profile
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to load profile from JSON: {e}")
            raise
    
    def load_from_dict(self, profile_data: Dict[str, Any]) -> FullProfile:
        """Load a profile from dictionary.
        
        Args:
            profile_data: Dictionary containing profile data
            
        Returns:
            FullProfile: Loaded profile
            
        Raises:
            ValidationError: If profile data is invalid

        """
        try:
            # Validate structure
            validation_result = self.validate_structure(profile_data)
            if not validation_result['valid']:
                raise ValueError(f"Profile structure validation failed: {validation_result['errors']}")
            
            # Create profile
            profile = FullProfile(**profile_data)
            
            logger.info("Successfully loaded profile from dictionary")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load profile from dictionary: {e}")
            raise
    
    def validate_structure(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure of profile data.
        
        Args:
            profile_data: Dictionary containing profile data
            
        Returns:
            Dict with validation result containing 'valid', 'errors', and 'warnings'

        """
        errors = []
        warnings = []
        
        # Check if it's a dictionary
        if not isinstance(profile_data, dict):
            errors.append("Profile data must be a dictionary")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check required top-level sections
        required_sections = ['subscriptions', 'export']
        optional_sections = ['filters', 'routing', 'agent', 'ui', 'legacy']
        
        for section in required_sections:
            if section not in profile_data:
                errors.append(f"Required section '{section}' is missing")
            elif section == 'subscriptions':
                # subscriptions is a list, not a dict
                if not isinstance(profile_data[section], list):
                    errors.append(f"Section '{section}' must be a list")
            elif not isinstance(profile_data[section], dict):
                errors.append(f"Section '{section}' must be a dictionary")
        
        # Check optional sections
        for section in optional_sections:
            if section in profile_data and not isinstance(profile_data[section], dict):
                errors.append(f"Section '{section}' must be a dictionary")
        
        # Validate subscription section
        if 'subscriptions' in profile_data and isinstance(profile_data['subscriptions'], dict):
            sub_errors = SECTION_VALIDATORS['subscriptions'].validate(profile_data['subscriptions'])
            errors.extend(sub_errors)
        
        # Validate export section
        if 'export' in profile_data and isinstance(profile_data['export'], dict):
            export_errors = SECTION_VALIDATORS['export'].validate(profile_data['export'])
            errors.extend(export_errors)
        
        # Validate filter section
        if 'filters' in profile_data and isinstance(profile_data['filters'], dict):
            filter_errors = SECTION_VALIDATORS['filters'].validate(profile_data['filters'])
            errors.extend(filter_errors)
        
        # Check for unknown sections
        known_sections = required_sections + optional_sections
        for section in profile_data:
            if section not in known_sections:
                warnings.append(f"Unknown section '{section}' - will be ignored")
        
        logger.debug(f"Structure validation: {len(errors)} errors, {len(warnings)} warnings")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_profile_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a profile file without loading it completely.
        
        Args:
            file_path: Path to the profile file
            
        Returns:
            Dict containing profile information

        """
        path = Path(file_path).expanduser().resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {file_path}")
        
        try:
            stat = path.stat()
            
            # Load just the basic structure to get info
            if path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:  # yaml/yml
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            
            # Extract basic info
            info = {
                'path': str(path),
                'name': path.stem,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'format': path.suffix.lower(),
                'sections': list(data.keys()) if isinstance(data, dict) else [],
                'valid': False,
                'error': None
            }
            
            # Try to validate
            try:
                validation_result = self.validate_structure(data)
                info['valid'] = validation_result['valid']
                info['error'] = '; '.join(validation_result['errors']) if validation_result['errors'] else None
            except Exception as e:
                info['valid'] = False
                info['error'] = str(e)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get profile info for {file_path}: {e}")
            raise
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON data from file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Dict containing loaded data

        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML data from file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Dict containing loaded data

        """
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def normalize_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize profile data in-place (e.g., convert string to list in filters).

        Args:
            profile_data: Profile data dict
        Returns:
            Normalized profile data dict

        """
        data = dict(profile_data)  # shallow copy
        # Normalize filters section
        filters_section = data.get('filters')
        if isinstance(filters_section, dict):
            # Convert string to list for tag fields
            for key in ('exclude_tags', 'only_tags', 'exclusions'):
                if key in filters_section and isinstance(filters_section[key], str):
                    filters_section[key] = [filters_section[key]]
        return data 