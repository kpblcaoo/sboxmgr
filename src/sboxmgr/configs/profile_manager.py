"""Profile management system for sboxmgr (ADR-0020).

This module provides the ProfileManager class for managing FullProfile configurations,
including creation, loading, validation, and active profile management.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .models import FullProfile, ValidationResult
from .templates import PROFILE_TEMPLATES


# Lazy logger initialization to avoid import-time logging setup requirement
def _get_logger():
    """Get logger for this module.

    Returns:
        Logger instance or None if logging not initialized.

    """
    try:
        from ..logging.core import get_logger

        return get_logger(__name__)
    except RuntimeError:
        # Fallback to basic logging if not initialized
        import logging

        return logging.getLogger(__name__)


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

    def __init__(
        self,
        path: str,
        name: str,
        size: int,
        modified: datetime,
        valid: bool = True,
        error: Optional[str] = None,
    ):
        """Initialize ProfileInfo.

        Args:
            path: Path to the profile file
            name: Profile name (derived from filename)
            size: File size in bytes
            modified: Last modification time
            valid: Whether the profile is valid
            error: Error message if profile is invalid

        """
        self.path = path
        self.name = name
        self.size = size
        self.modified = modified
        self.valid = valid
        self.error = error


class ProfileManager:
    """Central manager for FullProfile operations (ADR-0020).

    This class provides methods for creating, loading, saving, and validating
    FullProfile configurations. It also manages the active profile and provides
    profile listing with template support.

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
        self.profiles_dir = Path(
            profiles_dir or "~/.config/sboxmgr/profiles"
        ).expanduser()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.active_profile: Optional[FullProfile] = None
        self.profile_cache: dict[str, FullProfile] = {}
        self.active_profile_file = self.profiles_dir / ".active_profile"

        logger = _get_logger()
        if logger:
            logger.info(
                f"ProfileManager initialized with profiles directory: {self.profiles_dir}"
            )

        # Load active profile from file
        self._load_active_profile_from_file()

    def create_profile(self, name: str, template: Optional[str] = None) -> FullProfile:
        """Create a new profile with optional template.

        Args:
            name: Profile name
            template: Template name (basic, vpn, server) or None for empty

        Returns:
            FullProfile: Created profile

        Raises:
            ValueError: If template is invalid
            ValidationError: If profile data is invalid

        """
        logger = _get_logger()

        # Get template data
        if template:
            if template not in PROFILE_TEMPLATES:
                raise ValueError(f"Invalid template: {template}")
            template_data = PROFILE_TEMPLATES[template]["template"].copy()
        else:
            template_data = {}

        # Create profile data
        profile_data = {
            "id": name,
            "description": f"Profile created from template: {template}"
            if template
            else None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **template_data,
        }

        try:
            profile = FullProfile(**profile_data)
            if logger:
                logger.info(f"Created new profile: {profile.id} (template: {template})")
            return profile
        except ValidationError as e:
            if logger:
                logger.error(f"Failed to create profile: {e}")
            raise

    def get_profile(self, name: str) -> Optional[FullProfile]:
        """Get profile by name.

        Args:
            name: Profile name

        Returns:
            FullProfile or None: Profile if found, None otherwise

        """
        # Check cache first
        if name in self.profile_cache:
            return self.profile_cache[name]

        # Try to load from file
        profile_path = self.profiles_dir / f"{name}.toml"
        if not profile_path.exists():
            return None

        try:
            profile = self.load_profile(str(profile_path))
            self.profile_cache[name] = profile
            return profile
        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.error(f"Failed to load profile {name}: {e}")
            return None

    def save_profile(self, profile: FullProfile) -> None:
        """Save profile to file.

        Args:
            profile: Profile to save

        """
        logger = _get_logger()

        # Update timestamps
        profile.updated_at = datetime.now().isoformat()
        if not profile.created_at:
            profile.created_at = profile.updated_at

        # Save to file
        profile_path = self.profiles_dir / f"{profile.id}.toml"
        try:
            # Import here to avoid circular imports
            from .toml_support import save_toml

            save_toml(profile.model_dump(), profile_path)
            self.profile_cache[profile.id] = profile

            if logger:
                logger.info(f"Saved profile: {profile.id}")

        except Exception as e:
            if logger:
                logger.error(f"Failed to save profile {profile.id}: {e}")
            raise

    def delete_profile(self, name: str) -> bool:
        """Delete profile by name.

        Args:
            name: Profile name to delete

        Returns:
            bool: True if profile was deleted

        """
        logger = _get_logger()

        profile_path = self.profiles_dir / f"{name}.toml"
        if not profile_path.exists():
            return False

        try:
            profile_path.unlink()
            if name in self.profile_cache:
                del self.profile_cache[name]

            # If this was the active profile, clear it
            if self.active_profile and self.active_profile.id == name:
                self.active_profile = None
                self._save_active_profile_to_file("")

            if logger:
                logger.info(f"Deleted profile: {name}")

            return True

        except Exception as e:
            if logger:
                logger.error(f"Failed to delete profile {name}: {e}")
            return False

    def get_active_profile(self) -> Optional[FullProfile]:
        """Get the currently active profile.

        Returns:
            FullProfile or None: Active profile if set, None otherwise

        """
        return self.active_profile

    def get_active_profile_name(self) -> Optional[str]:
        """Get the name of currently active profile.

        Returns:
            str or None: Active profile name if set, None otherwise

        """
        if self.active_profile:
            return self.active_profile.id
        return None

    def set_active_profile(self, name: str) -> bool:
        """Set the active profile by name.

        Args:
            name: Profile name to set as active

        Returns:
            bool: True if profile was set as active

        """
        profile = self.get_profile(name)
        if not profile:
            return False

        self.active_profile = profile
        self._save_active_profile_to_file(name)

        logger = _get_logger()
        if logger:
            logger.info(f"Set active profile: {name}")

        return True

    def list_profiles(self) -> list[ProfileInfo]:
        """List all available profiles.

        Returns:
            list[ProfileInfo]: List of profile information

        """
        profiles = []
        logger = _get_logger()

        for file_path in self.profiles_dir.glob("*.toml"):
            if file_path.name.startswith("."):
                continue  # Skip hidden files

            name = file_path.stem
            stat = file_path.stat()

            # Check if profile is valid
            valid = True
            error = None
            try:
                self.get_profile(name)
            except Exception as e:
                valid = False
                error = str(e)

            profile_info = ProfileInfo(
                path=str(file_path),
                name=name,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                valid=valid,
                error=error,
            )
            profiles.append(profile_info)

        if logger:
            logger.debug(f"Found {len(profiles)} profiles")

        return profiles

    def load_profile(self, file_path: str) -> FullProfile:
        """Load profile from file.

        Args:
            file_path: Path to profile file

        Returns:
            FullProfile: Loaded profile

        Raises:
            ValidationError: If profile data is invalid

        """
        logger = _get_logger()

        try:
            # Import here to avoid circular imports
            from .toml_support import load_toml

            data = load_toml(file_path)
            profile = FullProfile(**data)

            if logger:
                logger.info(f"Loaded profile: {profile.id}")

            return profile

        except Exception as e:
            if logger:
                logger.error(f"Failed to load profile from {file_path}: {e}")
            raise

    def validate_profile(self, profile: FullProfile) -> ValidationResult:
        """Validate profile configuration.

        Args:
            profile: Profile to validate

        Returns:
            ValidationResult: Validation result with errors and warnings

        """
        errors = []
        warnings = []

        # Basic validation (Pydantic handles most of this)
        try:
            # Trigger validation by accessing model data
            profile.model_dump()
        except ValidationError as e:
            errors.extend(str(error) for error in e.errors())

        # Custom validation rules
        if not profile.subscriptions:
            warnings.append("No subscriptions configured")

        if not profile.export.output_file:
            warnings.append("No output file specified in export config")

        # Check for duplicate subscription IDs
        subscription_ids = [sub.id for sub in profile.subscriptions]
        if len(subscription_ids) != len(set(subscription_ids)):
            errors.append("Duplicate subscription IDs found")

        valid = len(errors) == 0

        logger = _get_logger()
        if logger:
            if valid:
                logger.debug(f"Profile {profile.id} validation passed")
            else:
                logger.warning(f"Profile {profile.id} validation failed: {errors}")

        return ValidationResult(valid=valid, errors=errors, warnings=warnings)

    def clear_cache(self) -> None:
        """Clear profile cache."""
        self.profile_cache.clear()
        logger = _get_logger()
        if logger:
            logger.debug("Profile cache cleared")

    def get_available_templates(self) -> list[str]:
        """Get list of available profile templates.

        Returns:
            list[str]: List of template names

        """
        return list(PROFILE_TEMPLATES.keys())

    def save_profile_to_file(self, profile: FullProfile, file_path: str) -> None:
        """Save profile to specific file path.

        Args:
            profile: Profile to save
            file_path: Path to save the profile to

        """
        logger = _get_logger()

        try:
            # Import here to avoid circular imports
            from .toml_support import save_toml

            save_toml(profile.model_dump(), Path(file_path))

            if logger:
                logger.info(f"Saved profile {profile.id} to {file_path}")

        except Exception as e:
            if logger:
                logger.error(f"Failed to save profile {profile.id} to {file_path}: {e}")
            raise

    def load_profile_from_file(self, file_path: str) -> FullProfile:
        """Load profile from specific file path.

        Args:
            file_path: Path to profile file

        Returns:
            FullProfile: Loaded profile

        Raises:
            ValidationError: If profile data is invalid

        """
        logger = _get_logger()

        try:
            # Import here to avoid circular imports
            from .toml_support import load_toml

            data = load_toml(file_path)
            profile = FullProfile(**data)

            if logger:
                logger.info(f"Loaded profile from {file_path}: {profile.id}")

            return profile

        except Exception as e:
            if logger:
                logger.error(f"Failed to load profile from {file_path}: {e}")
            raise

    def _load_active_profile_from_file(self) -> None:
        """Load active profile name from file."""
        if not self.active_profile_file.exists():
            return

        try:
            active_name = self.active_profile_file.read_text().strip()
            if active_name:
                profile = self.get_profile(active_name)
                if profile:
                    self.active_profile = profile
                    logger = _get_logger()
                    if logger:
                        logger.info(f"Loaded active profile: {active_name}")

        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.error(f"Failed to load active profile: {e}")

    def _save_active_profile_to_file(self, profile_name: str) -> None:
        """Save active profile name to file.

        Args:
            profile_name: Name of active profile

        """
        try:
            self.active_profile_file.write_text(profile_name)
        except Exception as e:
            logger = _get_logger()
            if logger:
                logger.error(f"Failed to save active profile: {e}")
