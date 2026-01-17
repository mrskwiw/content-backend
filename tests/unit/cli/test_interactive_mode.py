"""Tests for Interactive Mode"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.cli.interactive_mode import InteractiveMode
from src.models.brief_quality import BriefQualityReport, FieldQuality
from src.models.client_brief import ClientBrief, Platform, TonePreference
from src.models.question import Question, QuestionType


@pytest.fixture
def sample_quality_report():
    """Create sample quality report for testing"""
    return BriefQualityReport(
        overall_score=0.85,
        completeness_score=0.9,
        specificity_score=0.8,
        usability_score=0.85,
        can_generate_content=True,
        total_fields=20,
        filled_fields=18,
        required_fields_filled=15,
        minimum_questions_needed=0,
        field_quality={
            "company_name": FieldQuality.STRONG,
            "business_description": FieldQuality.ADEQUATE,
        },
        missing_fields=[],
        weak_fields=[],
    )


class TestInteractiveModeInit:
    """Test InteractiveMode initialization"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_init_creates_all_agents(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test initialization creates all required agents"""
        mode = InteractiveMode()

        assert mode.parser is not None
        assert mode.quality_checker is not None
        assert mode.question_generator is not None
        assert mode.enhancer is not None
        assert mode.client_brief is None
        assert mode.iteration_count == 0

        # Verify agents were created
        mock_parser.assert_called_once()
        mock_quality_checker.assert_called_once()
        mock_question_gen.assert_called_once()
        mock_enhancer.assert_called_once()


class TestLoadInitialBrief:
    """Test _load_initial_brief method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Progress")
    @patch("src.cli.interactive_mode.console")
    def test_load_initial_brief_success(
        self,
        mock_console,
        mock_progress,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test loading initial brief successfully"""
        # Create mock brief
        sample_brief = ClientBrief(
            company_name="Test Company",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        # Mock parser
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_brief.return_value = sample_brief
        mock_parser.return_value = mock_parser_instance

        # Mock file reading
        with patch("pathlib.Path.read_text", return_value="Brief content"):
            mode = InteractiveMode()
            result = mode._load_initial_brief("tests/fixtures/sample_brief.txt")

        assert result.company_name == "Test Company"
        mock_parser_instance.parse_brief.assert_called_once_with("Brief content")
        mock_console.print.assert_called()

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_load_initial_brief_failure_fallback(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test loading brief failure falls back to creating minimal brief"""
        # Mock parser to raise exception
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_brief.side_effect = Exception("Parse error")
        mock_parser.return_value = mock_parser_instance

        # Mock user prompts
        mock_prompt.ask.side_effect = ["Test Co", "Test biz", "Test customer", "Test problem"]

        with patch("pathlib.Path.read_text", return_value="Bad content"):
            mode = InteractiveMode()
            result = mode._load_initial_brief("bad_file.txt")

        assert result.company_name == "Test Co"
        assert "Failed to load brief" in str(mock_console.print.call_args_list)


class TestCreateMinimalBrief:
    """Test _create_minimal_brief method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_create_minimal_brief_with_all_answers(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test creating minimal brief with all answers provided"""
        mock_prompt.ask.side_effect = [
            "Test Company",
            "We do testing",
            "Test customers",
            "We solve test problems",
        ]

        mode = InteractiveMode()
        result = mode._create_minimal_brief()

        assert result.company_name == "Test Company"
        assert result.business_description == "We do testing"
        assert result.ideal_customer == "Test customers"
        assert result.main_problem_solved == "We solve test problems"

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_create_minimal_brief_with_defaults(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test creating minimal brief with default empty values"""
        mock_prompt.ask.side_effect = ["Test Company", "", "", ""]

        mode = InteractiveMode()
        result = mode._create_minimal_brief()

        assert result.company_name == "Test Company"
        assert result.business_description == "No description provided"
        assert result.ideal_customer == "Not specified"
        assert result.main_problem_solved == "Not specified"


class TestParseListInput:
    """Test _parse_list_input method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_parse_comma_separated(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test parsing comma-separated list"""
        mode = InteractiveMode()
        result = mode._parse_list_input("item1, item2, item3")

        assert result == ["item1", "item2", "item3"]

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_parse_newline_separated(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test parsing newline-separated list"""
        mode = InteractiveMode()
        result = mode._parse_list_input("- item1\n- item2\n- item3")

        assert result == ["item1", "item2", "item3"]

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_parse_numbered_list(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test parsing numbered list"""
        mode = InteractiveMode()
        result = mode._parse_list_input("1. item1 2. item2 3. item3")

        assert "item1" in result
        assert "item2" in result
        assert "item3" in result

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_parse_single_item(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test parsing single item"""
        mode = InteractiveMode()
        result = mode._parse_list_input("single item")

        assert result == ["single item"]


class TestUpdateBriefField:
    """Test _update_brief_field method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_string_field(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test updating a string field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Old desc",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._update_brief_field("business_description", "New description")

        assert mode.client_brief.business_description == "New description"

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_string_field_append(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test appending to string field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Old desc",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._update_brief_field("business_description", "Additional info", append=True)

        assert mode.client_brief.business_description == "Old desc Additional info"

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_list_field(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test updating a list field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._update_brief_field("customer_pain_points", "pain1, pain2, pain3")

        assert len(mode.client_brief.customer_pain_points) == 3
        assert "pain1" in mode.client_brief.customer_pain_points

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_list_field_append(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test appending to list field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
            customer_pain_points=["existing_pain"],
        )

        mode._update_brief_field("customer_pain_points", "new_pain", append=True)

        assert len(mode.client_brief.customer_pain_points) == 2
        assert "existing_pain" in mode.client_brief.customer_pain_points
        assert "new_pain" in mode.client_brief.customer_pain_points

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_brand_personality_field(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test updating brand_personality enum field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._update_brief_field("brand_personality", "conversational, direct")

        assert len(mode.client_brief.brand_personality) == 2
        assert TonePreference.CONVERSATIONAL in mode.client_brief.brand_personality
        assert TonePreference.DIRECT in mode.client_brief.brand_personality

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_update_target_platforms_field(
        self, mock_console, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test updating target_platforms enum field"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._update_brief_field("target_platforms", "linkedin, twitter")

        assert len(mode.client_brief.target_platforms) == 2
        assert Platform.LINKEDIN in mode.client_brief.target_platforms
        assert Platform.TWITTER in mode.client_brief.target_platforms


class TestAskSingleQuestion:
    """Test _ask_single_question method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_ask_question_with_answer(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test asking question and receiving answer (priority 3 - no follow-up)"""
        mock_prompt.ask.return_value = "Test answer"

        # Mock question generator to not generate follow-ups
        mock_question_gen_instance = MagicMock()
        mock_question_gen_instance.generate_follow_up_question.return_value = None
        mock_question_gen.return_value = mock_question_gen_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        question = Question(
            text="What's your business description?",
            field_name="business_description",
            question_type=QuestionType.OPEN_ENDED,
            priority=3,  # Priority 3 - no follow-up
        )

        mode._ask_single_question(question, 1, 1)

        assert mode.client_brief.business_description == "Test answer"
        mock_prompt.ask.assert_called()

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_ask_question_skip(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test skipping a question"""
        mock_prompt.ask.return_value = "[skip]"

        # Mock question generator (not used but required)
        mock_question_gen_instance = MagicMock()
        mock_question_gen.return_value = mock_question_gen_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Original",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        question = Question(
            text="What's your business description?",
            field_name="business_description",
            question_type=QuestionType.OPEN_ENDED,
            priority=3,  # Priority 3 so no follow-up attempt
        )

        mode._ask_single_question(question, 1, 1)

        # Should not have changed
        assert mode.client_brief.business_description == "Original"

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Prompt")
    @patch("src.cli.interactive_mode.console")
    def test_ask_question_with_follow_up(
        self,
        mock_console,
        mock_prompt,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test asking question with follow-up"""
        mock_prompt.ask.side_effect = ["Test answer", "Follow-up answer"]

        # Mock follow-up question generation
        mock_question_gen_instance = MagicMock()
        follow_up = Question(
            text="Follow-up question?",
            field_name="business_description",
            question_type=QuestionType.CLARIFYING,
            priority=1,
        )
        mock_question_gen_instance.generate_follow_up_question.return_value = follow_up
        mock_question_gen.return_value = mock_question_gen_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        question = Question(
            text="What's your business description?",
            field_name="business_description",
            question_type=QuestionType.OPEN_ENDED,
            priority=1,
        )

        mode._ask_single_question(question, 1, 1)

        # Should have both answers combined
        assert "Test answer" in mode.client_brief.business_description
        assert "Follow-up answer" in mode.client_brief.business_description


class TestConfirmReady:
    """Test _confirm_ready method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Confirm")
    @patch("src.cli.interactive_mode.console")
    def test_confirm_ready_proceed(
        self,
        mock_console,
        mock_confirm,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test user confirms ready to proceed"""
        mock_confirm.ask.return_value = True

        mode = InteractiveMode()

        result = mode._confirm_ready(sample_quality_report)

        assert result is True
        mock_confirm.ask.assert_called_once()

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Confirm")
    @patch("src.cli.interactive_mode.console")
    def test_confirm_ready_continue_improving(
        self,
        mock_console,
        mock_confirm,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test user wants to continue improving"""
        mock_confirm.ask.return_value = False

        mode = InteractiveMode()

        result = mode._confirm_ready(sample_quality_report)

        assert result is False


class TestSaveProgress:
    """Test _save_progress method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_progress_success(
        self,
        mock_file,
        mock_mkdir,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test saving progress successfully"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Company",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._save_progress()

        mock_mkdir.assert_called_once()
        mock_file.assert_called()
        # Check that filename contains company name
        call_args = mock_file.call_args[0][0]
        assert "Test_Company_wip.json" in str(call_args)


class TestSaveFinalBrief:
    """Test _save_final_brief method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_final_brief_success(
        self,
        mock_file,
        mock_mkdir,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
    ):
        """Test saving final brief successfully"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Company",
            business_description="Test business",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        result = mode._save_final_brief()

        mock_mkdir.assert_called_once()
        mock_file.assert_called()
        assert "Test_Company" in result
        assert "_complete.txt" in result


class TestFormatBriefAsText:
    """Test _format_brief_as_text method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_format_brief_minimal(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test formatting minimal brief"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Company",
            business_description="We do testing",
            ideal_customer="Test customers",
            main_problem_solved="Test problems",
        )

        result = mode._format_brief_as_text()

        assert "# Client Brief - Test Company" in result
        assert "Company: Test Company" in result
        assert "Business: We do testing" in result
        assert "Ideal Customer: Test customers" in result
        assert "Problem Solved: Test problems" in result

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    def test_format_brief_with_optional_fields(
        self, mock_question_gen, mock_quality_checker, mock_parser, mock_enhancer
    ):
        """Test formatting brief with optional fields"""
        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Company",
            business_description="We do testing",
            ideal_customer="Test customers",
            main_problem_solved="Test problems",
            founder_name="John Doe",
            website="https://example.com",
            brand_personality=[TonePreference.CONVERSATIONAL, TonePreference.DIRECT],
            key_phrases=["phrase1", "phrase2"],
            customer_pain_points=["pain1", "pain2"],
            customer_questions=["question1"],
            misconceptions=["myth1"],
            stories=["story1"],
            main_cta="Contact us",
        )

        result = mode._format_brief_as_text()

        assert "Founder: John Doe" in result
        assert "Website: https://example.com" in result
        assert "Personality:" in result
        assert "Key Phrases:" in result
        assert "Pain Points:" in result
        assert "- pain1" in result
        assert "Customer Questions:" in result
        assert "Misconceptions to Correct:" in result
        assert "Stories:" in result
        assert "Main CTA: Contact us" in result


class TestDisplayCompletion:
    """Test _display_completion method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_display_completion(
        self,
        mock_console,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test displaying completion message"""
        # Mock quality checker
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = sample_quality_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Company",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._display_completion("data/briefs/Test_Company_complete.txt")

        # Check that completion message was printed
        assert mock_console.print.called


class TestConversationLoop:
    """Test _conversation_loop method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Confirm")
    @patch("src.cli.interactive_mode.console")
    def test_conversation_loop_brief_ready(
        self,
        mock_console,
        mock_confirm,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test conversation loop when brief is ready"""
        # Mock quality checker to return ready status
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = sample_quality_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        # Mock user confirms ready
        mock_confirm.ask.return_value = True

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        with patch.object(mode, "_save_progress"):
            mode._conversation_loop()

        assert mode.iteration_count == 1

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.console")
    def test_conversation_loop_no_questions(
        self,
        mock_console,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test conversation loop when no questions generated"""
        # Create modified report with can_generate_content=False
        not_ready_report = BriefQualityReport(
            **{
                **sample_quality_report.model_dump(),
                "can_generate_content": False,
                "minimum_questions_needed": 2,
            }
        )

        # Mock quality checker
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = not_ready_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        # Mock question generator to return empty list
        mock_question_gen_instance = MagicMock()
        mock_question_gen_instance.generate_questions.return_value = []
        mock_question_gen.return_value = mock_question_gen_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        with patch.object(mode, "_save_progress"):
            mode._conversation_loop()

        # Should complete after 1 iteration
        assert mode.iteration_count == 1


class TestApplyFinalEnhancements:
    """Test _apply_final_enhancements method"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Progress")
    @patch("src.cli.interactive_mode.console")
    def test_apply_final_enhancements_success(
        self,
        mock_console,
        mock_progress,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test applying final enhancements successfully"""
        # Mock quality checker
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = sample_quality_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        # Mock enhancer
        enhanced_brief = ClientBrief(
            company_name="Test Co Enhanced",
            business_description="Enhanced description",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )
        mock_enhancer_instance = MagicMock()
        mock_enhancer_instance.enhance_brief.return_value = enhanced_brief
        mock_enhancer.return_value = mock_enhancer_instance

        mode = InteractiveMode()
        mode.client_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )

        mode._apply_final_enhancements()

        assert mode.client_brief.company_name == "Test Co Enhanced"
        mock_enhancer_instance.enhance_brief.assert_called_once()

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Progress")
    @patch("src.cli.interactive_mode.console")
    def test_apply_final_enhancements_failure(
        self,
        mock_console,
        mock_progress,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test handling enhancement failure"""
        # Mock quality checker
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = sample_quality_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        # Mock enhancer to raise exception
        mock_enhancer_instance = MagicMock()
        mock_enhancer_instance.enhance_brief.side_effect = Exception("Enhancement failed")
        mock_enhancer.return_value = mock_enhancer_instance

        mode = InteractiveMode()
        original_brief = ClientBrief(
            company_name="Test Co",
            business_description="Test",
            ideal_customer="Test customer",
            main_problem_solved="Test problem",
        )
        mode.client_brief = original_brief

        mode._apply_final_enhancements()

        # Brief should remain unchanged
        assert mode.client_brief == original_brief


class TestRun:
    """Test run method - main entry point"""

    @patch("src.cli.interactive_mode.BriefEnhancerAgent")
    @patch("src.cli.interactive_mode.BriefParserAgent")
    @patch("src.cli.interactive_mode.BriefQualityChecker")
    @patch("src.cli.interactive_mode.QuestionGeneratorAgent")
    @patch("src.cli.interactive_mode.Confirm")
    @patch("src.cli.interactive_mode.Progress")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.cli.interactive_mode.console")
    def test_run_with_keyboard_interrupt(
        self,
        mock_console,
        mock_file,
        mock_mkdir,
        mock_progress,
        mock_confirm,
        mock_question_gen,
        mock_quality_checker,
        mock_parser,
        mock_enhancer,
        sample_quality_report,
    ):
        """Test run method handles KeyboardInterrupt"""
        # Create modified report with can_generate_content=False
        not_ready_report = BriefQualityReport(
            **{
                **sample_quality_report.model_dump(),
                "can_generate_content": False,
                "minimum_questions_needed": 2,
            }
        )

        # Mock quality checker
        mock_quality_checker_instance = MagicMock()
        mock_quality_checker_instance.assess_brief.return_value = not_ready_report
        mock_quality_checker.return_value = mock_quality_checker_instance

        # Mock question generator to raise KeyboardInterrupt
        mock_question_gen_instance = MagicMock()
        mock_question_gen_instance.generate_questions.side_effect = KeyboardInterrupt()
        mock_question_gen.return_value = mock_question_gen_instance

        mode = InteractiveMode()

        with patch("src.cli.interactive_mode.Prompt.ask", side_effect=["Test Co", "", "", ""]):
            mode.run()

        # Should print interrupted message
        assert any("interrupted" in str(call).lower() for call in mock_console.print.call_args_list)
