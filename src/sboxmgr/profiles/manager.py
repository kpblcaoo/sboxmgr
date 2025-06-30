"""Profile management system for sboxmgr.

This module provides the ProfileManager class for managing profiles,
including creation, loading, validation, and active profile management.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from pydantic import ValidationError

from ..profiles.models import FullProfile
from ..logging.core import get_logger

logger = get_logger(__name__)


class ProfileInfo:
    """Information about a profile file.
    
    Attributes:
        path: Path to the profile file
        name: Profile name (derived from filename)
        size: File size in bytes
        modified: Last modification time
        valid: Whether the profile is valid
        error: Error message if profile is invalid
    """
    
    def __init__(self, path: str, name: str, size: int, modified: datetime, 
                 valid: bool = True, error: Optional[str] = None):
        self.path = path
        self.name = name
        self.size = size
        self.modified = modified
        self.valid = valid
        self.error = error


class ValidationResult:
    """Result of profile validation.
    
    Attributes:
        valid: Whether the profile is valid
        errors: List of validation errors
        warnings: List of validation warnings
    """
    
    def __init__(self, valid: bool = True, errors: Optional[List[str]] = None, 
                 warnings: Optional[List[str]] = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []


class ProfileManager:
    """Central manager for profile operations.
    
    This class provides methods for creating, loading, saving, and validating
    profiles. It also manages the active profile and provides profile listing.
    
    Attributes:
        profiles_dir: Directory for storing profiles
        active_profile: Currently active profile
        profile_cache: Cache of loaded profiles
    """
    
    def __init__(self, profiles_dir: Optional[str] = None):
        """Initialize the ProfileManager.
        
        Args:
            profiles_dir: Directory for storing profiles. If None, uses default.
        """
        self.profiles_dir = Path(profiles_dir or "~/.config/sboxmgr/profiles").expanduser()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_profile: Optional[FullProfile] = None
        self.profile_cache: Dict[str, FullProfile] = {}
        
        logger.info(f"ProfileManager initialized with profiles directory: {self.profiles_dir}")
    
    def create_profile(self, profile_data: dict) -> FullProfile:
        """Create a new profile from dictionary data.
        
        Args:
            profile_data: Dictionary containing profile data
            
        Returns:
            FullProfile: Created profile
            
        Raises:
            ValidationError: If profile data is invalid
        """
        try:
            profile = FullProfile(**profile_data)
            logger.info(f"Created new profile: {profile.name if hasattr(profile, 'name') else 'unnamed'}")
            return profile
        except ValidationError as e:
            logger.error(f"Failed to create profile: {e}")
            raise
    
    def load_profile(self, profile_path: str) -> FullProfile:
        """Load a profile from file.
        
        Args:
            profile_path: Path to the profile file
            
        Returns:
            FullProfile: Loaded profile
            
        Raises:
            FileNotFoundError: If profile file doesn't exist
            ValidationError: If profile data is invalid
        """
        path = Path(profile_path).expanduser().resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {profile_path}")
        
        # Check cache first
        cache_key = str(path)
        if cache_key in self.profile_cache:
            logger.debug(f"Loading profile from cache: {profile_path}")
            return self.profile_cache[cache_key]
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            profile = self.create_profile(profile_data)
            
            # Cache the profile
            self.profile_cache[cache_key] = profile
            
            logger.info(f"Loaded profile from file: {profile_path}")
            return profile
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in profile file {profile_path}: {e}")
            raise ValueError(f"Invalid JSON in profile file: {e}")
        except Exception as e:
            logger.error(f"Failed to load profile from {profile_path}: {e}")
            raise
    
    def save_profile(self, profile: FullProfile, path: str) -> None:
        """Save a profile to file.
        
        Args:
            profile: Profile to save
            path: Path where to save the profile
            
        Raises:
            OSError: If file cannot be written
        """
        file_path = Path(path).expanduser().resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert to dict with JSON-compatible values
            profile_dict = profile.model_dump(mode='json')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)
            
            # Update cache
            cache_key = str(file_path)
            self.profile_cache[cache_key] = profile
            
            logger.info(f"Saved profile to file: {path}")
            
        except Exception as e:
            logger.error(f"Failed to save profile to {path}: {e}")
            raise OSError(f"Failed to save profile: {e}")
    
    def validate_profile(self, profile: FullProfile) -> ValidationResult:
        """Validate a profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            ValidationResult: Validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        try:
            # Pydantic validation is already done, but we can add custom validation here
            profile.model_validate(profile.model_dump())
            
            # Custom validation rules
            if hasattr(profile, 'subscriptions') and profile.subscriptions:
                # Validate subscription sources
                for subscription in profile.subscriptions:
                    if not hasattr(subscription, 'id') or not subscription.id:
                        errors.append(f"Subscription must have valid ID")
            
            if hasattr(profile, 'export') and profile.export:
                # Validate export settings
                if profile.export.format not in ['sing-box', 'clash', 'json']:
                    errors.append(f"Unsupported output format: {profile.export.format}")
            
            logger.debug(f"Profile validation completed: {len(errors)} errors, {len(warnings)} warnings")
            
        except ValidationError as e:
            errors.extend([str(error) for error in e.errors()])
            logger.error(f"Profile validation failed: {e}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_active_profile(self) -> Optional[FullProfile]:
        """Get the currently active profile.
        
        Returns:
            FullProfile or None: Active profile if set, None otherwise
        """
        return self.active_profile
    
    def set_active_profile(self, profile: FullProfile) -> None:
        """Set the active profile.
        
        Args:
            profile: Profile to set as active
        """
        self.active_profile = profile
        logger.info(f"Set active profile: {profile.name if hasattr(profile, 'name') else 'unnamed'}")
    
    def list_profiles(self) -> List[ProfileInfo]:
        """List all available profiles in the profiles directory.
        
        Returns:
            List[ProfileInfo]: List of profile information
        """
        profiles = []
        
        if not self.profiles_dir.exists():
            return profiles
        
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                stat = file_path.stat()
                name = file_path.stem
                
                # Try to validate the profile
                try:
                    self.load_profile(str(file_path))
                    valid = True
                    error = None
                except Exception as e:
                    valid = False
                    error = str(e)
                
                profile_info = ProfileInfo(
                    path=str(file_path),
                    name=name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    valid=valid,
                    error=error
                )
                
                profiles.append(profile_info)
                
            except Exception as e:
                logger.warning(f"Failed to get info for profile {file_path}: {e}")
        
        logger.debug(f"Found {len(profiles)} profiles in {self.profiles_dir}")
        return profiles
    
    def clear_cache(self) -> None:
        """Clear the profile cache."""
        self.profile_cache.clear()
        logger.debug("Profile cache cleared") 