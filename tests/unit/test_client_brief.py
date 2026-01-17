"""Unit tests for client_brief module.

Tests cover:
- Platform enum case-insensitive lookup
- ClientBrief field validation
- get_missing_fields method
- to_context_dict method
"""

import pytest
from pydantic import ValidationError

from src.models.client_brief import (
    ClientBrief,
    Platform,
    TonePreference,
    DataUsagePreference,
)


class TestPlatformEnum:
    """Tests for Platform enum."""

    def test_platform_case_insensitive_lookup(self):
        """Test that Platform enum handles case-insensitive lookup."""
        # Lowercase
        assert Platform("linkedin") == Platform.LINKEDIN
        # Uppercase
        assert Platform("LINKEDIN") == Platform.LINKEDIN
        # Mixed case
        assert Platform("LinkedIn") == Platform.LINKEDIN
        assert Platform("Twitter") == Platform.TWITTER
        assert Platform("FaceBook") == Platform.FACEBOOK

    def test_platform_missing_value_returns_none(self):
        """Test that invalid platform returns None via _missing_."""
        # Invalid platform should trigger _missing_ and return None
        result = Platform._missing_("invalid_platform")
        assert result is None

    def test_platform_values(self):
        """Test platform values."""
        assert Platform.LINKEDIN.value == "linkedin"
        assert Platform.TWITTER.value == "twitter"
        assert Platform.FACEBOOK.value == "facebook"
        assert Platform.BLOG.value == "blog"
        assert Platform.EMAIL.value == "email"
        assert Platform.MULTI.value == "multi"


class TestClientBriefValidation:
    """Tests for ClientBrief validation."""

    def test_customer_questions_limit_exceeded(self):
        """Test that customer_questions list with >10 items raises ValueError (line 113)."""
        with pytest.raises(ValidationError) as exc_info:
            ClientBrief(
                company_name="Test Co",
                business_description="Test business",
                ideal_customer="Test customer",
                main_problem_solved="Test problem",
                customer_questions=[f"Question {i}" for i in range(15)],  # 15 items > 10
            )

        assert "at most 10 items" in str(exc_info.value)

    def test_customer_questions_at_limit(self):
        """Test that exactly 10 customer_questions is valid."""
        brief = ClientBrief(
            company_name="Test Co",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
            customer_questions=[f"Question {i}" for i in range(10)],  # Exactly 10
        )
        assert len(brief.customer_questions) == 10

    def test_required_fields_only(self):
        """Test creating brief with only required fields."""
        brief = ClientBrief(
            company_name="Test Company",
            business_description="We do testing",
            ideal_customer="Testers",
            main_problem_solved="Testing issues",
        )
        assert brief.company_name == "Test Company"
        assert brief.founder_name is None
        assert brief.stories == []
        assert brief.data_usage == DataUsagePreference.MODERATE


class TestGetMissingFields:
    """Tests for get_missing_fields method (lines 116-127)."""

    def test_all_fields_missing(self):
        """Test get_missing_fields when all optional fields are missing."""
        brief = ClientBrief(
            company_name="Test Co",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
            # All optional fields that get_missing_fields checks are missing
        )

        missing = brief.get_missing_fields()

        assert "founder_name" in missing
        assert "stories (needed for personal story templates)" in missing
        assert "main_cta" in missing
        assert "measurable_results" in missing

    def test_no_fields_missing(self):
        """Test get_missing_fields when all optional fields are present."""
        brief = ClientBrief(
            company_name="Test Co",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
            founder_name="John Doe",
            stories=["Story 1", "Story 2"],
            main_cta="Learn more",
            measurable_results="50% improvement",
        )

        missing = brief.get_missing_fields()

        assert missing == []

    def test_some_fields_missing(self):
        """Test get_missing_fields with partial fields."""
        brief = ClientBrief(
            company_name="Test Co",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
            founder_name="Jane Doe",  # Present
            stories=["A story"],  # Present
            # main_cta is missing
            # measurable_results is missing
        )

        missing = brief.get_missing_fields()

        assert "founder_name" not in missing
        assert "stories (needed for personal story templates)" not in missing
        assert "main_cta" in missing
        assert "measurable_results" in missing


class TestToContextDict:
    """Tests for to_context_dict method."""

    def test_to_context_dict_basic(self):
        """Test to_context_dict with basic fields."""
        brief = ClientBrief(
            company_name="Test Company",
            business_description="We solve problems",
            ideal_customer="Small business owners",
            main_problem_solved="Workflow inefficiency",
        )

        context = brief.to_context_dict()

        assert context["company_name"] == "Test Company"
        assert context["ideal_customer"] == "Small business owners"
        assert context["problem_solved"] == "Workflow inefficiency"
        assert context["main_cta"] == "engage with us"  # Default when None
        assert context["data_preference"] == "moderate"
        assert context["brand_voice"] == ""  # Empty list
        assert context["pain_points"] == []
        assert context["key_phrases"] == []
        assert context["stories"] == []

    def test_to_context_dict_full(self):
        """Test to_context_dict with all fields populated."""
        brief = ClientBrief(
            company_name="Full Company",
            business_description="Complete solution",
            ideal_customer="Enterprise clients",
            main_problem_solved="Complex problems",
            brand_personality=[TonePreference.AUTHORITATIVE, TonePreference.DIRECT],
            customer_pain_points=["Pain 1", "Pain 2"],
            key_phrases=["phrase one", "phrase two"],
            stories=["Story A", "Story B"],
            main_cta="Schedule a demo",
            data_usage=DataUsagePreference.HEAVY,
            misconceptions=["Myth 1"],
            customer_questions=["Q1", "Q2"],
            measurable_results="2x ROI",
        )

        context = brief.to_context_dict()

        assert context["company_name"] == "Full Company"
        assert context["brand_voice"] == "authoritative, direct"
        assert context["pain_points"] == ["Pain 1", "Pain 2"]
        assert context["key_phrases"] == ["phrase one", "phrase two"]
        assert context["stories"] == ["Story A", "Story B"]
        assert context["main_cta"] == "Schedule a demo"
        assert context["data_preference"] == "heavy"
        assert context["misconceptions"] == ["Myth 1"]
        assert context["customer_questions"] == ["Q1", "Q2"]
        assert context["results"] == "2x ROI"


class TestTonePreferenceEnum:
    """Tests for TonePreference enum."""

    def test_tone_values(self):
        """Test all tone preference values."""
        assert TonePreference.APPROACHABLE.value == "approachable"
        assert TonePreference.DIRECT.value == "direct"
        assert TonePreference.AUTHORITATIVE.value == "authoritative"
        assert TonePreference.WITTY.value == "witty"
        assert TonePreference.VULNERABLE.value == "vulnerable"
        assert TonePreference.DATA_DRIVEN.value == "data_driven"
        assert TonePreference.CONVERSATIONAL.value == "conversational"


class TestDataUsagePreferenceEnum:
    """Tests for DataUsagePreference enum."""

    def test_data_usage_values(self):
        """Test all data usage preference values."""
        assert DataUsagePreference.HEAVY.value == "heavy"
        assert DataUsagePreference.MODERATE.value == "moderate"
        assert DataUsagePreference.MINIMAL.value == "minimal"
