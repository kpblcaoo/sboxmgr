"""Data models for exclusion management."""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExclusionEntry(BaseModel):
    """Single exclusion entry."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExclusionList(BaseModel):
    """Collection of exclusions with metadata and versioning."""

    model_config = ConfigDict(extra="forbid")

    exclusions: List[ExclusionEntry] = Field(default_factory=list)
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
