"""Unit tests for ProfileLoader."""

import sys
from unittest.mock import MagicMock

sys.modules["src.sboxmgr.logging.core"] = MagicMock()


from src.sboxmgr.profiles.loader import (
    SECTION_VALIDATORS,
    ExportSectionValidator,
    FilterSectionValidator,
    ProfileLoader,
    ProfileSectionValidator,
    SubscriptionSectionValidator,
)


class TestProfileLoader:
    """Test ProfileLoader functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ProfileLoader()

    def test_normalize_profile_string_to_list(self):
        """Test normalize_profile converts string to list in filters."""
        # Test data with string values that should be converted to lists
        profile_data = {
            "id": "test-profile",
            "subscriptions": [],
            "export": {"format": "sing-box"},
            "filters": {
                "exclude_tags": "slow",  # Should become ["slow"]
                "only_tags": "premium",  # Should become ["premium"]
                "exclusions": "blocked",  # Should become ["blocked"]
            },
        }

        normalized = self.loader.normalize_profile(profile_data)

        # Check that strings were converted to lists
        assert normalized["filters"]["exclude_tags"] == ["slow"]
        assert normalized["filters"]["only_tags"] == ["premium"]
        assert normalized["filters"]["exclusions"] == ["blocked"]

    def test_normalize_profile_preserves_lists(self):
        """Test normalize_profile preserves existing lists."""
        profile_data = {
            "id": "test-profile",
            "subscriptions": [],
            "export": {"format": "sing-box"},
            "filters": {
                "exclude_tags": ["slow", "unstable"],  # Already a list
                "only_tags": ["premium", "fast"],  # Already a list
                "exclusions": ["blocked", "geo"],  # Already a list
            },
        }

        normalized = self.loader.normalize_profile(profile_data)

        # Check that lists were preserved
        assert normalized["filters"]["exclude_tags"] == ["slow", "unstable"]
        assert normalized["filters"]["only_tags"] == ["premium", "fast"]
        assert normalized["filters"]["exclusions"] == ["blocked", "geo"]

    def test_normalize_profile_handles_missing_sections(self):
        """Test normalize_profile handles missing filter sections gracefully."""
        profile_data = {
            "id": "test-profile",
            "subscriptions": [],
            "export": {"format": "sing-box"},
            # No filters section
        }

        normalized = self.loader.normalize_profile(profile_data)

        # Should not raise exception and return original data
        assert normalized == profile_data

    def test_normalize_profile_handles_partial_filters(self):
        """Test normalize_profile handles partial filter configurations."""
        profile_data = {
            "id": "test-profile",
            "subscriptions": [],
            "export": {"format": "sing-box"},
            "filters": {
                "exclude_tags": "slow"  # Only exclude_tags
                # No only_tags or exclusions
            },
        }

        normalized = self.loader.normalize_profile(profile_data)

        # Should convert string to list
        assert normalized["filters"]["exclude_tags"] == ["slow"]
        # Should not add missing fields
        assert "only_tags" not in normalized["filters"]
        assert "exclusions" not in normalized["filters"]


class TestSectionValidators:
    """Test profile section validators."""

    def test_subscription_section_validator_valid(self):
        """Test SubscriptionSectionValidator with valid data."""
        validator = SubscriptionSectionValidator()
        data = [
            {"id": "source1", "enabled": True, "priority": 1},
            {"id": "source2", "enabled": False, "priority": 2},
        ]

        errors = validator.validate(data)
        assert errors == []

    def test_subscription_section_validator_invalid_type(self):
        """Test SubscriptionSectionValidator with invalid type."""
        validator = SubscriptionSectionValidator()
        data = "not_a_list"

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be a list" in errors[0]

    def test_subscription_section_validator_missing_id(self):
        """Test SubscriptionSectionValidator with missing subscription ID."""
        validator = SubscriptionSectionValidator()
        data = [{"enabled": True, "priority": 1}]  # Missing id

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must have 'id' field" in errors[0]

    def test_subscription_section_validator_invalid_priority_type(self):
        """Test SubscriptionSectionValidator with invalid priority type."""
        validator = SubscriptionSectionValidator()
        data = [{"id": "source1", "priority": "high"}]  # Should be int

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be an integer" in errors[0]

    def test_export_section_validator_valid(self):
        """Test ExportSectionValidator with valid data."""
        validator = ExportSectionValidator()
        data = {"format": "sing-box", "output_file": "/path/to/output.json"}

        errors = validator.validate(data)
        assert errors == []

    def test_export_section_validator_invalid_format(self):
        """Test ExportSectionValidator with invalid format."""
        validator = ExportSectionValidator()
        data = {"format": "invalid_format"}

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be 'sing-box', 'clash', or 'json'" in errors[0]

    def test_export_section_validator_invalid_file_type(self):
        """Test ExportSectionValidator with invalid output file type."""
        validator = ExportSectionValidator()
        data = {"output_file": 123}  # Should be string

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be a string" in errors[0]

    def test_filter_section_validator_valid(self):
        """Test FilterSectionValidator with valid data."""
        validator = FilterSectionValidator()
        data = {
            "exclude_tags": ["slow", "unstable"],
            "only_tags": ["premium", "fast"],
            "exclusions": ["blocked", "geo"],
            "only_enabled": True,
        }

        errors = validator.validate(data)
        assert errors == []

    def test_filter_section_validator_invalid_tags_type(self):
        """Test FilterSectionValidator with invalid tags type."""
        validator = FilterSectionValidator()
        data = {"exclude_tags": "slow"}  # Should be list

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be a list" in errors[0]

    def test_filter_section_validator_invalid_enabled_type(self):
        """Test FilterSectionValidator with invalid only_enabled type."""
        validator = FilterSectionValidator()
        data = {"only_enabled": "yes"}  # Should be boolean

        errors = validator.validate(data)
        assert len(errors) == 1
        assert "must be a boolean" in errors[0]


class TestSectionValidatorsRegistry:
    """Test SECTION_VALIDATORS registry."""

    def test_section_validators_registry_contains_expected_validators(self):
        """Test that SECTION_VALIDATORS contains all expected validators."""
        expected_sections = ["subscriptions", "export", "filters"]

        for section in expected_sections:
            assert section in SECTION_VALIDATORS
            assert isinstance(SECTION_VALIDATORS[section], ProfileSectionValidator)

    def test_section_validators_registry_validate_methods(self):
        """Test that all validators in registry have validate method."""
        for _section, validator in SECTION_VALIDATORS.items():
            assert hasattr(validator, "validate")
            assert callable(validator.validate)

    def test_section_validators_registry_integration(self):
        """Test integration of validators in registry."""
        # Test that all validators work together
        test_data = {
            "subscriptions": [{"id": "test-sub", "enabled": True, "priority": 1}],
            "export": {"format": "sing-box", "output_file": "/tmp/test.json"},
            "filters": {
                "exclude_tags": ["slow"],
                "only_tags": ["premium"],
                "exclusions": ["blocked"],
                "only_enabled": True,
            },
        }

        # All validators should pass
        for section, validator in SECTION_VALIDATORS.items():
            if section in test_data:
                errors = validator.validate(test_data[section])
                assert errors == [], f"Validator for {section} failed: {errors}"
