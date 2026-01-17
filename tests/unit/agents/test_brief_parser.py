"""Unit tests for Brief Parser Agent"""

import json
import pytest
from unittest.mock import Mock, patch
from src.agents.brief_parser import BriefParserAgent
from src.models.client_brief import ClientBrief, Platform, TonePreference, DataUsagePreference
from src.exceptions import BriefParsingError


class TestBriefParserAgent:
    """Test suite for BriefParserAgent"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        return Mock()

    @pytest.fixture
    def brief_parser(self, mock_anthropic_client):
        """Create brief parser with mocked client"""
        return BriefParserAgent(client=mock_anthropic_client)

    @pytest.fixture
    def sample_brief_text(self):
        """Sample brief text input"""
        return """
        Company: Acme SaaS Inc
        Business: We provide cloud-based project management software for remote teams
        Ideal Customer: Tech startups with 10-50 employees
        Main Problem: Teams struggle to stay organized across multiple time zones
        Pain Points:
        - Missed deadlines due to poor coordination
        - Information silos between departments
        - Time wasted on status meetings
        """

    @pytest.fixture
    def sample_brief_json(self):
        """Sample brief JSON response from API"""
        return {
            "company_name": "Acme SaaS Inc",
            "business_description": "Cloud-based project management software for remote teams",
            "ideal_customer": "Tech startups with 10-50 employees",
            "main_problem_solved": "Teams struggle to stay organized across multiple time zones",
            "customer_pain_points": [
                "Missed deadlines due to poor coordination",
                "Information silos between departments",
                "Time wasted on status meetings",
            ],
            "customer_questions": [
                "How do I keep my remote team aligned?",
                "What's the best way to track project progress?",
            ],
            "brand_personality": ["authoritative", "approachable"],
            "key_phrases": ["async-first", "timezone-friendly", "seamless collaboration"],
            "target_platforms": ["linkedin", "twitter"],
            "posting_frequency": "3-4x weekly",
            "data_usage": "moderate",
            "stories": ["Launch story about first remote client"],
            "misconceptions": ["Project management tools are too complex"],
        }

    def test_initialization_with_client(self, mock_anthropic_client):
        """Test parser initializes with provided client"""
        parser = BriefParserAgent(client=mock_anthropic_client)
        assert parser.client == mock_anthropic_client

    def test_initialization_without_client(self):
        """Test parser creates default client if none provided"""
        with patch("src.agents.brief_parser.AnthropicClient") as MockClient:
            parser = BriefParserAgent()
            MockClient.assert_called_once()

    def test_parse_brief_success(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test successful brief parsing"""
        # Mock API response with JSON
        mock_anthropic_client.create_message.return_value = json.dumps(sample_brief_json)

        result = brief_parser.parse_brief(sample_brief_text)

        # Verify API call
        mock_anthropic_client.create_message.assert_called_once()
        call_kwargs = mock_anthropic_client.create_message.call_args[1]
        assert call_kwargs["messages"][0]["content"] == sample_brief_text
        assert "temperature" in call_kwargs

        # Verify result
        assert isinstance(result, ClientBrief)
        assert result.company_name == "Acme SaaS Inc"
        assert result.ideal_customer == "Tech startups with 10-50 employees"
        assert len(result.customer_pain_points) == 3

    def test_parse_brief_with_markdown_json(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test parsing JSON wrapped in markdown code blocks"""
        # Mock API response with markdown-wrapped JSON
        markdown_response = f"```json\n{json.dumps(sample_brief_json)}\n```"
        mock_anthropic_client.create_message.return_value = markdown_response

        result = brief_parser.parse_brief(sample_brief_text)

        assert isinstance(result, ClientBrief)
        assert result.company_name == "Acme SaaS Inc"

    def test_parse_brief_with_code_block_no_language(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test parsing JSON in code blocks without language specifier"""
        # Mock API response with code block but no 'json' marker
        code_block_response = f"```\n{json.dumps(sample_brief_json)}\n```"
        mock_anthropic_client.create_message.return_value = code_block_response

        result = brief_parser.parse_brief(sample_brief_text)

        assert isinstance(result, ClientBrief)
        assert result.company_name == "Acme SaaS Inc"

    def test_parse_brief_invalid_json(self, brief_parser, mock_anthropic_client, sample_brief_text):
        """Test parsing fails with invalid JSON"""
        # Mock API response with invalid JSON
        mock_anthropic_client.create_message.return_value = "This is not JSON"

        with pytest.raises(BriefParsingError) as exc_info:
            brief_parser.parse_brief(sample_brief_text)

        assert "Brief parsing failed" in str(exc_info.value)

    def test_parse_brief_api_error(self, brief_parser, mock_anthropic_client, sample_brief_text):
        """Test parsing handles API errors"""
        # Mock API error
        mock_anthropic_client.create_message.side_effect = Exception("API Error")

        with pytest.raises(BriefParsingError) as exc_info:
            brief_parser.parse_brief(sample_brief_text)

        assert "Brief parsing failed" in str(exc_info.value)

    def test_extract_json_from_response_plain_json(self, brief_parser, sample_brief_json):
        """Test extracting plain JSON from response"""
        response = json.dumps(sample_brief_json)
        result = brief_parser._extract_json_from_response(response)

        assert result == sample_brief_json

    def test_extract_json_from_response_markdown(self, brief_parser, sample_brief_json):
        """Test extracting JSON from markdown code block"""
        response = f"```json\n{json.dumps(sample_brief_json)}\n```"
        result = brief_parser._extract_json_from_response(response)

        assert result == sample_brief_json

    def test_extract_json_from_response_with_whitespace(self, brief_parser, sample_brief_json):
        """Test extracting JSON with extra whitespace"""
        response = f"\n\n  \n{json.dumps(sample_brief_json)}\n  \n"
        result = brief_parser._extract_json_from_response(response)

        assert result == sample_brief_json

    def test_extract_json_from_response_invalid(self, brief_parser):
        """Test extraction fails with invalid JSON"""
        with pytest.raises(ValueError) as exc_info:
            brief_parser._extract_json_from_response("not json at all")

        assert "Invalid JSON in response" in str(exc_info.value)

    def test_convert_to_client_brief_minimal(self, brief_parser):
        """Test converting minimal data to ClientBrief"""
        minimal_data = {
            "company_name": "Test Co",
            "business_description": "Test business",
            "ideal_customer": "Test customers",
            "main_problem_solved": "Test problem",
        }

        result = brief_parser._convert_to_client_brief(minimal_data)

        assert isinstance(result, ClientBrief)
        assert result.company_name == "Test Co"
        assert result.customer_pain_points == []
        assert result.brand_personality == []

    def test_convert_to_client_brief_full(self, brief_parser, sample_brief_json):
        """Test converting full data to ClientBrief"""
        result = brief_parser._convert_to_client_brief(sample_brief_json)

        assert isinstance(result, ClientBrief)
        assert result.company_name == "Acme SaaS Inc"
        assert result.ideal_customer == "Tech startups with 10-50 employees"
        assert len(result.customer_pain_points) == 3
        assert len(result.brand_personality) == 2
        assert TonePreference.AUTHORITATIVE in result.brand_personality
        assert TonePreference.APPROACHABLE in result.brand_personality

    def test_convert_brand_personality_to_enum(self, brief_parser):
        """Test brand personality strings converted to enum"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "brand_personality": ["direct", "conversational", "authoritative"],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert TonePreference.DIRECT in result.brand_personality
        assert TonePreference.CONVERSATIONAL in result.brand_personality
        assert TonePreference.AUTHORITATIVE in result.brand_personality

    def test_convert_brand_personality_invalid_skipped(self, brief_parser):
        """Test invalid brand personality values are skipped"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "brand_personality": ["direct", "invalid_value", "conversational"],
        }

        result = brief_parser._convert_to_client_brief(data)

        # Should have 2 valid values, 1 skipped
        assert len(result.brand_personality) == 2
        assert TonePreference.DIRECT in result.brand_personality
        assert TonePreference.CONVERSATIONAL in result.brand_personality

    def test_convert_platforms_to_enum(self, brief_parser):
        """Test platform strings converted to enum"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "target_platforms": ["linkedin", "twitter", "blog"],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert Platform.LINKEDIN in result.target_platforms
        assert Platform.TWITTER in result.target_platforms
        assert Platform.BLOG in result.target_platforms

    def test_convert_platforms_invalid_skipped(self, brief_parser):
        """Test invalid platform values are skipped"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "target_platforms": ["linkedin", "invalid_platform", "twitter"],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert len(result.target_platforms) == 2
        assert Platform.LINKEDIN in result.target_platforms
        assert Platform.TWITTER in result.target_platforms

    def test_convert_data_usage_enum(self, brief_parser):
        """Test data usage string converted to enum"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "data_usage": "minimal",
        }

        result = brief_parser._convert_to_client_brief(data)

        assert result.data_usage == DataUsagePreference.MINIMAL

    def test_convert_data_usage_defaults_to_moderate(self, brief_parser):
        """Test invalid data usage defaults to moderate"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "data_usage": "invalid_value",
        }

        result = brief_parser._convert_to_client_brief(data)

        assert result.data_usage == DataUsagePreference.MODERATE

    def test_convert_stories_field_mapping(self, brief_parser):
        """Test stories field maps from personal_stories"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "personal_stories": ["Story 1", "Story 2"],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert result.stories == ["Story 1", "Story 2"]

    def test_convert_misconceptions_field_mapping(self, brief_parser):
        """Test misconceptions field maps from avoid_topics"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "avoid_topics": ["Topic 1", "Topic 2"],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert result.misconceptions == ["Topic 1", "Topic 2"]

    def test_convert_defaults_for_missing_fields(self, brief_parser):
        """Test default values used for missing fields"""
        minimal_data = {}

        result = brief_parser._convert_to_client_brief(minimal_data)

        assert result.company_name == "Unknown Company"
        assert result.business_description == "No description provided"
        assert result.ideal_customer == "Not specified"
        assert result.main_problem_solved == "Not specified"
        assert result.posting_frequency == "3-4x weekly"

    def test_enrich_brief_success(self, brief_parser, mock_anthropic_client, sample_brief_json):
        """Test successfully enriching an existing brief"""
        # Create existing brief
        existing_brief = ClientBrief(
            company_name="Acme SaaS Inc",
            business_description="Project management software",
            ideal_customer="Startups",
            main_problem_solved="Organization",
        )

        # Mock API response with enriched data
        enriched_data = sample_brief_json.copy()
        enriched_data["customer_questions"].append("How secure is your platform?")
        mock_anthropic_client.create_message.return_value = json.dumps(enriched_data)

        additional_context = "Client also asks about security features frequently"
        result = brief_parser.enrich_brief(existing_brief, additional_context)

        # Verify API called with merge instructions
        mock_anthropic_client.create_message.assert_called_once()
        call_kwargs = mock_anthropic_client.create_message.call_args[1]
        assert "merge this new information" in call_kwargs["messages"][0]["content"]
        assert additional_context in call_kwargs["messages"][0]["content"]

        # Verify enriched result
        assert isinstance(result, ClientBrief)
        assert len(result.customer_questions) >= 2

    def test_enrich_brief_api_failure_returns_original(self, brief_parser, mock_anthropic_client):
        """Test enrichment failure returns original brief"""
        existing_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test",
            main_problem_solved="Test",
        )

        # Mock API error
        mock_anthropic_client.create_message.side_effect = Exception("API Error")

        result = brief_parser.enrich_brief(existing_brief, "Additional context")

        # Should return original brief
        assert result == existing_brief

    def test_enrich_brief_invalid_response_returns_original(
        self, brief_parser, mock_anthropic_client
    ):
        """Test enrichment with invalid response returns original"""
        existing_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test",
            main_problem_solved="Test",
        )

        # Mock invalid JSON response
        mock_anthropic_client.create_message.return_value = "invalid json"

        result = brief_parser.enrich_brief(existing_brief, "Additional context")

        # Should return original brief
        assert result == existing_brief

    def test_parse_brief_temperature_setting(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test brief parsing uses correct temperature"""
        mock_anthropic_client.create_message.return_value = json.dumps(sample_brief_json)

        brief_parser.parse_brief(sample_brief_text)

        call_kwargs = mock_anthropic_client.create_message.call_args[1]
        # Should use low temperature for accuracy
        assert call_kwargs["temperature"] <= 0.5

    def test_parse_brief_uses_system_prompt(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test brief parsing uses system prompt"""
        mock_anthropic_client.create_message.return_value = json.dumps(sample_brief_json)

        brief_parser.parse_brief(sample_brief_text)

        call_kwargs = mock_anthropic_client.create_message.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == BriefParserAgent.SYSTEM_PROMPT

    def test_convert_handles_empty_lists(self, brief_parser):
        """Test conversion handles empty list fields correctly"""
        data = {
            "company_name": "Test",
            "business_description": "Test",
            "ideal_customer": "Test",
            "main_problem_solved": "Test",
            "customer_pain_points": [],
            "customer_questions": [],
            "brand_personality": [],
            "key_phrases": [],
            "target_platforms": [],
            "stories": [],
            "misconceptions": [],
        }

        result = brief_parser._convert_to_client_brief(data)

        assert result.customer_pain_points == []
        assert result.customer_questions == []
        assert result.brand_personality == []
        assert result.key_phrases == []
        assert result.target_platforms == []
        assert result.stories == []
        assert result.misconceptions == []

    def test_parse_brief_logging(
        self, brief_parser, mock_anthropic_client, sample_brief_text, sample_brief_json
    ):
        """Test brief parsing logs appropriately"""
        mock_anthropic_client.create_message.return_value = json.dumps(sample_brief_json)

        with patch("src.agents.brief_parser.logger") as mock_logger:
            brief_parser.parse_brief(sample_brief_text)

            # Should log start and success
            assert mock_logger.info.call_count >= 2
