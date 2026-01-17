"""Unit tests for quality_profile module.

Tests cover:
- QualityProfile model creation and validation
- Validators for readability and word count
- to_dict() method
- from_file() and save_to_file() methods
- DEFAULT_PROFILES dictionary
- get_default_profile() function
"""

import json
import pytest

from src.models.quality_profile import (
    QualityProfile,
    DEFAULT_PROFILES,
    get_default_profile,
)


class TestQualityProfileModel:
    """Tests for QualityProfile model creation."""

    def test_create_basic_profile(self):
        """Test creating a basic quality profile."""
        profile = QualityProfile(
            profile_name="test_profile",
            description="Test description",
        )

        assert profile.profile_name == "test_profile"
        assert profile.description == "Test description"
        # Default values
        assert profile.min_readability == 50.0
        assert profile.max_readability == 65.0
        assert profile.min_words == 150
        assert profile.max_words == 300
        assert profile.min_engagement_score == 2
        assert profile.require_cta is True
        assert profile.max_attempts == 2
        assert profile.enabled is True

    def test_create_custom_profile(self):
        """Test creating a profile with custom values."""
        profile = QualityProfile(
            profile_name="custom",
            description="Custom profile",
            min_readability=40.0,
            max_readability=80.0,
            min_words=100,
            max_words=500,
            min_engagement_score=1,
            require_cta=False,
            max_attempts=3,
            enabled=False,
        )

        assert profile.min_readability == 40.0
        assert profile.max_readability == 80.0
        assert profile.min_words == 100
        assert profile.max_words == 500
        assert profile.min_engagement_score == 1
        assert profile.require_cta is False
        assert profile.max_attempts == 3
        assert profile.enabled is False

    def test_field_constraints(self):
        """Test field constraints are enforced."""
        # min_readability must be 0-100
        with pytest.raises(ValueError):
            QualityProfile(
                profile_name="test",
                description="test",
                min_readability=-1.0,
            )

        with pytest.raises(ValueError):
            QualityProfile(
                profile_name="test",
                description="test",
                min_readability=101.0,
            )

        # min_words must be 50-2000
        with pytest.raises(ValueError):
            QualityProfile(
                profile_name="test",
                description="test",
                min_words=10,
            )

        # max_attempts must be 1-5
        with pytest.raises(ValueError):
            QualityProfile(
                profile_name="test",
                description="test",
                max_attempts=0,
            )

        with pytest.raises(ValueError):
            QualityProfile(
                profile_name="test",
                description="test",
                max_attempts=10,
            )


class TestQualityProfileValidators:
    """Tests for QualityProfile validators."""

    def test_max_readability_must_exceed_min(self):
        """Test that max_readability must be greater than min_readability."""
        with pytest.raises(ValueError) as exc_info:
            QualityProfile(
                profile_name="test",
                description="test",
                min_readability=70.0,
                max_readability=50.0,  # Less than min
            )
        assert "must be greater than min_readability" in str(exc_info.value)

    def test_max_readability_equal_to_min_fails(self):
        """Test that max_readability equal to min_readability fails."""
        with pytest.raises(ValueError) as exc_info:
            QualityProfile(
                profile_name="test",
                description="test",
                min_readability=60.0,
                max_readability=60.0,  # Equal to min
            )
        assert "must be greater than min_readability" in str(exc_info.value)

    def test_max_words_must_exceed_min(self):
        """Test that max_words must be greater than min_words."""
        with pytest.raises(ValueError) as exc_info:
            QualityProfile(
                profile_name="test",
                description="test",
                min_words=300,
                max_words=150,  # Less than min
            )
        assert "must be greater than min_words" in str(exc_info.value)

    def test_max_words_equal_to_min_fails(self):
        """Test that max_words equal to min_words fails."""
        with pytest.raises(ValueError) as exc_info:
            QualityProfile(
                profile_name="test",
                description="test",
                min_words=200,
                max_words=200,  # Equal to min
            )
        assert "must be greater than min_words" in str(exc_info.value)


class TestQualityProfileToDict:
    """Tests for to_dict() method."""

    def test_to_dict_returns_all_fields(self):
        """Test that to_dict returns all fields."""
        profile = QualityProfile(
            profile_name="test",
            description="test desc",
            min_readability=45.0,
            max_readability=70.0,
        )

        result = profile.to_dict()

        assert isinstance(result, dict)
        assert result["profile_name"] == "test"
        assert result["description"] == "test desc"
        assert result["min_readability"] == 45.0
        assert result["max_readability"] == 70.0
        assert "min_words" in result
        assert "max_words" in result
        assert "min_engagement_score" in result
        assert "require_cta" in result
        assert "max_attempts" in result
        assert "enabled" in result


class TestQualityProfileFileOperations:
    """Tests for from_file() and save_to_file() methods."""

    def test_save_and_load_profile(self, tmp_path):
        """Test saving and loading a profile from file."""
        profile = QualityProfile(
            profile_name="file_test",
            description="Testing file operations",
            min_readability=55.0,
            max_readability=75.0,
            min_words=200,
            max_words=400,
        )

        file_path = tmp_path / "test_profile.json"
        profile.save_to_file(str(file_path))

        assert file_path.exists()

        loaded = QualityProfile.from_file(str(file_path))

        assert loaded.profile_name == profile.profile_name
        assert loaded.description == profile.description
        assert loaded.min_readability == profile.min_readability
        assert loaded.max_readability == profile.max_readability
        assert loaded.min_words == profile.min_words
        assert loaded.max_words == profile.max_words

    def test_save_creates_parent_directories(self, tmp_path):
        """Test that save_to_file creates parent directories."""
        profile = QualityProfile(
            profile_name="nested",
            description="test",
        )

        nested_path = tmp_path / "nested" / "dir" / "profile.json"
        profile.save_to_file(str(nested_path))

        assert nested_path.exists()

    def test_from_file_not_found(self):
        """Test from_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            QualityProfile.from_file("/nonexistent/path/profile.json")
        assert "Quality profile not found" in str(exc_info.value)

    def test_from_file_invalid_json(self, tmp_path):
        """Test from_file raises ValueError for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ not valid json }")

        with pytest.raises(ValueError) as exc_info:
            QualityProfile.from_file(str(file_path))
        assert "Invalid JSON" in str(exc_info.value)

    def test_from_file_missing_required_field(self, tmp_path):
        """Test from_file raises ValueError for missing required fields."""
        file_path = tmp_path / "incomplete.json"
        file_path.write_text('{"profile_name": "test"}')  # Missing description

        with pytest.raises(ValueError) as exc_info:
            QualityProfile.from_file(str(file_path))
        assert "Failed to load profile" in str(exc_info.value)

    def test_from_file_invalid_values(self, tmp_path):
        """Test from_file raises ValueError for invalid field values."""
        file_path = tmp_path / "invalid_values.json"
        # Invalid: min_readability > max_readability
        file_path.write_text(
            json.dumps(
                {
                    "profile_name": "test",
                    "description": "test",
                    "min_readability": 80.0,
                    "max_readability": 50.0,
                }
            )
        )

        with pytest.raises(ValueError) as exc_info:
            QualityProfile.from_file(str(file_path))
        assert "Failed to load profile" in str(exc_info.value)


class TestDefaultProfiles:
    """Tests for DEFAULT_PROFILES dictionary."""

    def test_expected_profiles_exist(self):
        """Test that expected default profiles exist."""
        expected = [
            "professional_linkedin",
            "casual_linkedin",
            "executive_linkedin",
            "twitter",
            "blog",
            "permissive",
        ]
        for profile_name in expected:
            assert profile_name in DEFAULT_PROFILES

    def test_profile_count(self):
        """Test the number of default profiles."""
        assert len(DEFAULT_PROFILES) == 6

    def test_all_profiles_are_valid(self):
        """Test that all default profiles are valid QualityProfile instances."""
        for name, profile in DEFAULT_PROFILES.items():
            assert isinstance(profile, QualityProfile)
            assert profile.profile_name == name

    def test_professional_linkedin_profile(self):
        """Test professional_linkedin profile settings."""
        profile = DEFAULT_PROFILES["professional_linkedin"]
        assert profile.min_readability == 50.0
        assert profile.max_readability == 65.0
        assert profile.min_words == 150
        assert profile.max_words == 300
        assert profile.require_cta is True
        assert profile.enabled is True

    def test_twitter_profile(self):
        """Test twitter profile has concise settings."""
        profile = DEFAULT_PROFILES["twitter"]
        assert profile.min_words == 50
        assert profile.max_words == 100
        assert profile.min_readability == 65.0  # Higher readability for Twitter

    def test_blog_profile(self):
        """Test blog profile has longer content settings."""
        profile = DEFAULT_PROFILES["blog"]
        assert profile.min_words == 800
        assert profile.max_words == 2000

    def test_permissive_profile(self):
        """Test permissive profile has relaxed settings."""
        profile = DEFAULT_PROFILES["permissive"]
        assert profile.min_engagement_score == 0
        assert profile.require_cta is False
        assert profile.max_attempts == 1
        assert profile.enabled is False  # Disabled by default


class TestGetDefaultProfile:
    """Tests for get_default_profile() function."""

    def test_get_professional_linkedin(self):
        """Test getting professional_linkedin profile."""
        profile = get_default_profile("professional_linkedin")
        assert profile.profile_name == "professional_linkedin"

    def test_get_default_without_arg(self):
        """Test getting default profile without argument."""
        profile = get_default_profile()
        assert profile.profile_name == "professional_linkedin"

    def test_get_all_valid_profiles(self):
        """Test getting all valid profile names."""
        for name in DEFAULT_PROFILES.keys():
            profile = get_default_profile(name)
            assert profile.profile_name == name

    def test_invalid_profile_raises_error(self):
        """Test that invalid profile name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_default_profile("nonexistent_profile")
        assert "Unknown profile" in str(exc_info.value)
        assert "nonexistent_profile" in str(exc_info.value)
        # Should list available profiles
        assert "professional_linkedin" in str(exc_info.value)


class TestQualityProfileConfig:
    """Tests for model config."""

    def test_json_schema_has_example(self):
        """Test that JSON schema includes an example."""
        schema = QualityProfile.model_json_schema()
        assert "example" in schema or "examples" in schema

    def test_model_serialization(self):
        """Test model serialization to JSON."""
        profile = QualityProfile(
            profile_name="serialize_test",
            description="test serialization",
        )

        json_str = profile.model_dump_json()
        data = json.loads(json_str)

        assert data["profile_name"] == "serialize_test"
        assert data["description"] == "test serialization"
