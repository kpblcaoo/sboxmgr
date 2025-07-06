"""Pydantic models for exclusion management.

Implements ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation.
Replaces dataclass-based models with Pydantic BaseModel for better validation and schema generation.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ExclusionEntryModel(BaseModel):
    """Single exclusion entry with Pydantic validation.
    
    Implements validation for exclusion entries with proper timestamp handling
    and JSON schema generation capability.
    """
    
    id: str = Field(..., description="Unique identifier for the excluded server")
    name: Optional[str] = Field(None, description="Human-readable name for the exclusion")
    reason: Optional[str] = Field(None, description="Reason for exclusion")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when exclusion was created"
    )
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that ID is not empty."""
        if not v.strip():
            raise ValueError("Exclusion ID cannot be empty")
        return v.strip()
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v) -> datetime:
        """Validate and normalize timestamp."""
        if isinstance(v, str):
            # Handle ISO format strings
            try:
                # Replace Z with +00:00 for fromisoformat
                v = v.replace("Z", "+00:00")
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}")
        elif isinstance(v, datetime):
            # Ensure timezone awareness
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        else:
            raise ValueError(f"Invalid timestamp type: {type(v)}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON serialization

        """
        return {
            "id": self.id,
            "name": self.name,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z")
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExclusionEntryModel':
        """Create from dictionary (JSON deserialization).
        
        Args:
            data: Dictionary containing exclusion entry data
            
        Returns:
            ExclusionEntryModel instance
            
        Raises:
            ValueError: If required fields are missing or invalid

        """
        return cls(**data)


class ExclusionListModel(BaseModel):
    """Collection of exclusions with metadata and versioning.
    
    Implements validation for exclusion lists with proper versioning support
    and JSON schema generation capability.
    """
    
    exclusions: List[ExclusionEntryModel] = Field(
        default_factory=list,
        description="List of exclusion entries"
    )
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last modification"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Schema version for migration support"
    )
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: int) -> int:
        """Validate version number."""
        if v < 1:
            raise ValueError("Version must be >= 1")
        return v
    
    @field_validator('last_modified', mode='before')
    @classmethod
    def validate_last_modified(cls, v) -> datetime:
        """Validate and normalize last_modified timestamp."""
        if isinstance(v, str):
            try:
                v = v.replace("Z", "+00:00")
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid last_modified format: {v}")
        elif isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        else:
            raise ValueError(f"Invalid last_modified type: {type(v)}")
    
    @model_validator(mode='after')
    def validate_exclusion_ids_unique(self) -> 'ExclusionListModel':
        """Validate that all exclusion IDs are unique."""
        ids = [ex.id for ex in self.exclusions]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate exclusion IDs found")
        return self
    
    def add(self, entry: ExclusionEntryModel) -> bool:
        """Add exclusion entry.
        
        Args:
            entry: Exclusion entry to add
            
        Returns:
            True if added, False if already exists

        """
        if any(ex.id == entry.id for ex in self.exclusions):
            return False
        
        self.exclusions.append(entry)
        self.last_modified = datetime.now(timezone.utc)
        return True
    
    def remove(self, server_id: str) -> bool:
        """Remove exclusion by server ID.
        
        Args:
            server_id: ID of server to remove from exclusions
            
        Returns:
            True if removed, False if not found

        """
        original_count = len(self.exclusions)
        self.exclusions = [ex for ex in self.exclusions if ex.id != server_id]
        
        if len(self.exclusions) < original_count:
            self.last_modified = datetime.now(timezone.utc)
            return True
        return False
    
    def contains(self, server_id: str) -> bool:
        """Check if server is excluded.
        
        Args:
            server_id: ID of server to check
            
        Returns:
            True if server is excluded, False otherwise

        """
        return any(ex.id == server_id for ex in self.exclusions)
    
    def clear(self) -> int:
        """Clear all exclusions.
        
        Returns:
            Number of exclusions cleared

        """
        count = len(self.exclusions)
        self.exclusions.clear()
        if count > 0:
            self.last_modified = datetime.now(timezone.utc)
        return count
    
    def get_ids(self) -> set[str]:
        """Get set of excluded server IDs.
        
        Returns:
            Set of server IDs that are excluded

        """
        return {ex.id for ex in self.exclusions}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON serialization

        """
        return {
            "version": self.version,
            "last_modified": self.last_modified.isoformat().replace("+00:00", "Z"),
            "exclusions": [ex.to_dict() for ex in self.exclusions]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExclusionListModel':
        """Create from dictionary (JSON deserialization) with version migration.
        
        Args:
            data: Dictionary containing exclusion list data
            
        Returns:
            ExclusionListModel instance
            
        Raises:
            ValueError: If data is invalid or migration fails

        """
        # Handle versioning and migrations
        version = data.get("version", 0)  # 0 = legacy format
        
        if version == 0:
            # Legacy format without version - migrate to v1
            version = 1
        elif version > 1:
            # Future version - log warning but try to load
            import logging
            logging.warning(f"Exclusion file version {version} is newer than supported (1). Attempting to load...")
        
        # Prepare data for Pydantic model
        model_data = {
            "version": version,
            "last_modified": data.get("last_modified", ""),
            "exclusions": [
                ExclusionEntryModel.from_dict(ex_data)
                for ex_data in data.get("exclusions", [])
            ]
        }
        
        return cls(**model_data)
