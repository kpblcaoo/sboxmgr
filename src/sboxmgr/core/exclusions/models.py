"""Data models for exclusion management."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional


@dataclass
class ExclusionEntry:
    """Single exclusion entry."""
    
    id: str
    name: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z")
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExclusionEntry':
        """Create from dictionary (JSON deserialization)."""
        timestamp = data.get("timestamp")
        if timestamp:
            # Handle both old format and new format
            if isinstance(timestamp, str):
                # Try to parse ISO format
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
            
        return cls(
            id=data["id"],
            name=data.get("name"),
            reason=data.get("reason"),
            timestamp=timestamp
        )


@dataclass
class ExclusionList:
    """Collection of exclusions with metadata and versioning."""
    
    exclusions: List[ExclusionEntry] = field(default_factory=list)
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1  # For future migrations
    
    def add(self, entry: ExclusionEntry) -> bool:
        """Add exclusion entry.
        
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
        """Check if server is excluded."""
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
    
    def get_ids(self) -> set:
        """Get set of excluded server IDs."""
        return {ex.id for ex in self.exclusions}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "last_modified": self.last_modified.isoformat().replace("+00:00", "Z"),
            "exclusions": [ex.to_dict() for ex in self.exclusions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExclusionList':
        """Create from dictionary (JSON deserialization) with version migration."""
        # Handle versioning and migrations
        version = data.get("version", 0)  # 0 = legacy format
        
        if version == 0:
            # Legacy format without version - migrate to v1
            version = 1
        elif version > 1:
            # Future version - log warning but try to load
            import logging
            logging.warning(f"Exclusion file version {version} is newer than supported (1). Attempting to load...")
        
        last_modified = data.get("last_modified", "")
        if last_modified:
            try:
                last_modified = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
            except ValueError:
                last_modified = datetime.now(timezone.utc)
        else:
            last_modified = datetime.now(timezone.utc)
        
        exclusions = [
            ExclusionEntry.from_dict(ex_data) 
            for ex_data in data.get("exclusions", [])
        ]
        
        return cls(
            exclusions=exclusions,
            last_modified=last_modified,
            version=version
        ) 