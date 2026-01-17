"""Unit tests for Content Generator Agent

This test suite focuses on the key methods and logic paths in ContentGeneratorAgent.
Some complex integration scenarios are tested in integration tests.
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.content_generator import ContentGeneratorAgent
from src.models.client_brief import ClientBrief, Platform
from src.models.post import Post
from src.models.template import Template, TemplateType, TemplateDifficulty
from src.models.seo_keyword import KeywordStrategy, SEOKeyword, KeywordIntent, KeywordDifficulty


class TestContentGeneratorAgent:
    """Test suite for ContentGeneratorAgent"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        return Mock()

    @pytest.fixture
    def mock_template_loader(self):
        """Mock template loader"""
        loader = Mock()
        # Mock template objects
        loader.select_templates_for_client.return_value = [
            Template(
                template_id=1,
                name="Template 1",
                structure="Test structure 1",
                template_type=TemplateType.PROBLEM_RECOGNITION,
                difficulty=TemplateDifficulty.FAST,
                best_for="Awareness",
            ),
            Template(
                template_id=2,
                name="Template 2",
                structure="Test structure 2",
                template_type=TemplateType.STATISTIC,
                difficulty=TemplateDifficulty.MEDIUM,
                best_for="Authority",
            ),
        ]
        loader.get_template_by_id.side_effect = lambda tid: Template(
            template_id=tid,
            name=f"Template {tid}",
            structure=f"Structure {tid}",
            template_type=TemplateType.PROBLEM_RECOGNITION,
            difficulty=TemplateDifficulty.FAST,
            best_for="General",
        )
        return loader

    @pytest.fixture
    def content_generator(self, mock_anthropic_client, mock_template_loader):
        """Create content generator with mocked dependencies"""
        return ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
        )

    @pytest.fixture
    def sample_client_brief(self):
        """Sample client brief"""
        return ClientBrief(
            company_name="Test Company",
            business_description="Test business providing test services",
            ideal_customer="Test customers who need test solutions",
            main_problem_solved="Solving test problems efficiently",
            customer_pain_points=["Pain point 1", "Pain point 2"],
        )

    @pytest.fixture
    def sample_template(self):
        """Sample template"""
        return Template(
            template_id=1,
            name="Test Template",
            structure="[HOOK]\n\n[PROBLEM]\n\n[SOLUTION]\n\nCTA: [CALL_TO_ACTION]",
            template_type=TemplateType.PROBLEM_RECOGNITION,
            difficulty=TemplateDifficulty.FAST,
            best_for="Awareness building",
        )

    @pytest.fixture
    def sample_keyword_strategy(self):
        """Sample keyword strategy"""
        return KeywordStrategy(
            primary_keywords=[
                SEOKeyword(
                    keyword="test keyword",
                    intent=KeywordIntent.INFORMATIONAL,
                    difficulty=KeywordDifficulty.EASY,
                    priority=1,
                ),
                SEOKeyword(
                    keyword="example",
                    intent=KeywordIntent.COMMERCIAL,
                    difficulty=KeywordDifficulty.MEDIUM,
                    priority=2,
                ),
            ],
            secondary_keywords=[
                SEOKeyword(
                    keyword="demo",
                    intent=KeywordIntent.INFORMATIONAL,
                    difficulty=KeywordDifficulty.EASY,
                    priority=3,
                ),
            ],
            longtail_keywords=[
                SEOKeyword(
                    keyword="how to test",
                    intent=KeywordIntent.INFORMATIONAL,
                    difficulty=KeywordDifficulty.EASY,
                    priority=4,
                ),
            ],
        )

    def test_initialization_with_dependencies(self, mock_anthropic_client, mock_template_loader):
        """Test generator initializes with provided dependencies"""
        generator = ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
        )

        assert generator.client == mock_anthropic_client
        assert generator.template_loader == mock_template_loader
        assert generator.keyword_strategy is None
        assert generator.db is None

    def test_initialization_with_keyword_strategy(
        self, mock_anthropic_client, mock_template_loader, sample_keyword_strategy
    ):
        """Test generator initializes with keyword strategy"""
        keyword_strategy = sample_keyword_strategy

        generator = ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
            keyword_strategy=keyword_strategy,
        )

        assert generator.keyword_strategy == keyword_strategy

    def test_initialization_defaults(self):
        """Test generator creates default dependencies if not provided"""
        with (
            patch("src.agents.content_generator.AnthropicClient") as MockClient,
            patch("src.agents.content_generator.TemplateLoader") as MockLoader,
        ):

            generator = ContentGeneratorAgent()

            MockClient.assert_called_once()
            MockLoader.assert_called_once()

    def test_generate_posts_with_template_quantities(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test generate_posts with template_quantities parameter"""
        template_quantities = {1: 3, 2: 5}

        with patch.object(content_generator, "_generate_posts_from_quantities") as mock_gen:
            mock_gen.return_value = [Mock(spec=Post)] * 8

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                template_quantities=template_quantities,
            )

            # Should call _generate_posts_from_quantities
            mock_gen.assert_called_once()
            assert len(result) == 8

    def test_generate_posts_legacy_mode(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test generate_posts in legacy equal distribution mode"""
        # Mock the template selection
        mock_template_loader.select_templates_for_client.return_value = [
            Template(
                template_id=1,
                name="Template 1",
                structure="Test",
                template_type=TemplateType.PROBLEM_RECOGNITION,
                difficulty=TemplateDifficulty.FAST,
                best_for="Awareness",
            ),
            Template(
                template_id=2,
                name="Template 2",
                structure="Test",
                template_type=TemplateType.STATISTIC,
                difficulty=TemplateDifficulty.MEDIUM,
                best_for="Authority",
            ),
        ]

        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            # Mock post generation
            mock_gen_single.return_value = Post(
                content="Test post",
                template_id=1,
                template_name="Template 1",
                client_name="Test Company",
            )

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=4,
                template_count=2,
                randomize=False,
            )

            # Should generate 4 posts (2 templates x 2 uses each)
            assert len(result) == 4
            # Should call _generate_single_post 4 times
            assert mock_gen_single.call_count == 4

    def test_generate_posts_template_selection_intelligent(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test intelligent template selection is used by default"""
        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=4,
                template_count=2,
            )

            # Verify intelligent selection was called
            mock_template_loader.select_templates_for_client.assert_called_once()
            call_args = mock_template_loader.select_templates_for_client.call_args
            assert call_args[0][0] == sample_client_brief
            assert call_args[1]["count"] == 2

    def test_generate_posts_manual_template_ids(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test manual template ID override"""
        template_ids = [1, 3, 5]

        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=6,
                template_ids=template_ids,
            )

            # Should use get_template_by_id for each ID
            assert mock_template_loader.get_template_by_id.call_count == len(template_ids)

    def test_generate_posts_manual_template_ids_invalid(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test manual template IDs with invalid IDs raises error"""
        # Mock get_template_by_id to return None for all IDs
        # Need to override side_effect, not just return_value
        mock_template_loader.get_template_by_id.side_effect = lambda tid: None

        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=6,
                template_ids=[99, 100],  # Invalid IDs
            )

        assert "No valid templates found" in str(exc_info.value)

    def test_generate_posts_randomization(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test post randomization"""
        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            # Create posts with predictable order
            mock_gen_single.side_effect = [
                Post(content=f"Post {i}", template_id=1, template_name="Test", client_name="Test")
                for i in range(4)
            ]

            # Generate with randomize=True
            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=4,
                randomize=True,
            )

            # Can't test exact randomization, but verify we got all posts
            assert len(result) == 4

    def test_generate_posts_no_randomization(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test posts stay in order when randomize=False"""
        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.side_effect = [
                Post(content=f"Post {i}", template_id=1, template_name="Test", client_name="Test")
                for i in range(4)
            ]

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=4,
                randomize=False,
            )

            # Order should be preserved
            assert result[0].content == "Post 0"
            assert result[1].content == "Post 1"

    def test_generate_posts_platform_parameter(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test platform parameter is passed to post generation"""
        with (
            patch.object(content_generator, "_generate_single_post") as mock_gen_single,
            patch.object(content_generator, "_build_system_prompt") as mock_build_prompt,
        ):

            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )
            mock_build_prompt.return_value = "System prompt"

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
                platform=Platform.TWITTER,
            )

            # Verify platform passed to _build_system_prompt
            mock_build_prompt.assert_called_once()
            assert mock_build_prompt.call_args[0][1] == Platform.TWITTER

    def test_generate_posts_uses_per_template_calculation(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test correct calculation of uses per template"""
        # 30 posts / 15 templates = 2 uses per template
        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            # Mock 15 templates
            mock_template_loader.select_templates_for_client.return_value = [
                Template(
                    template_id=i,
                    name=f"Template {i}",
                    structure="Test",
                    template_type=TemplateType.PROBLEM_RECOGNITION,
                    difficulty=TemplateDifficulty.FAST,
                    best_for="Test",
                )
                for i in range(1, 16)
            ]

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=30,
                template_count=15,
            )

            # Should generate exactly 30 posts
            assert len(result) == 30
            assert mock_gen_single.call_count == 30

    def test_generate_posts_extra_posts_distribution(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test extra posts distributed correctly"""
        # 31 posts / 15 templates = 2 uses each + 1 extra
        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            mock_template_loader.select_templates_for_client.return_value = [
                Template(
                    template_id=i,
                    name=f"Template {i}",
                    structure="Test",
                    template_type=TemplateType.PROBLEM_RECOGNITION,
                    difficulty=TemplateDifficulty.FAST,
                    best_for="Test",
                )
                for i in range(1, 16)
            ]

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=31,
                template_count=15,
            )

            # Should generate exactly 31 posts
            assert len(result) == 31

    @pytest.mark.asyncio
    async def test_generate_posts_async_with_template_quantities(
        self, content_generator, sample_client_brief
    ):
        """Test async generation with template quantities"""
        template_quantities = {1: 3, 2: 5}

        with patch.object(content_generator, "_generate_posts_from_quantities_async") as mock_gen:
            mock_gen.return_value = [Mock(spec=Post)] * 8

            result = await content_generator.generate_posts_async(
                client_brief=sample_client_brief,
                template_quantities=template_quantities,
            )

            # Should call async version
            mock_gen.assert_called_once()
            assert len(result) == 8

    @pytest.mark.asyncio
    async def test_generate_posts_async_concurrency_limit(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test async generation respects concurrency limit"""
        with patch.object(
            content_generator, "_generate_single_post_with_retry_async"
        ) as mock_gen_single:
            # Mock async post generation
            async def mock_generate(*args, **kwargs):
                return Post(
                    content="Test",
                    template_id=1,
                    template_name="Test",
                    client_name="Test",
                )

            mock_gen_single.side_effect = mock_generate

            result = await content_generator.generate_posts_async(
                client_brief=sample_client_brief,
                num_posts=4,
                max_concurrent=5,
            )

            # Should generate all posts
            assert len(result) == 4
            # Each post generated via async method
            assert mock_gen_single.call_count == 4

    @pytest.mark.asyncio
    async def test_generate_posts_async_randomization(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test async generation randomizes when requested"""
        with patch.object(
            content_generator, "_generate_single_post_with_retry_async"
        ) as mock_gen_single:

            async def mock_generate(*args, **kwargs):
                # Generate posts with predictable content
                post_num = mock_gen_single.call_count
                return Post(
                    content=f"Post {post_num}",
                    template_id=1,
                    template_name="Test",
                    client_name="Test",
                )

            mock_gen_single.side_effect = mock_generate

            result = await content_generator.generate_posts_async(
                client_brief=sample_client_brief,
                num_posts=4,
                randomize=True,
            )

            # All posts generated
            assert len(result) == 4

    def test_detect_cta_static_method(self):
        """Test _detect_cta static method"""
        # Test various CTA indicators
        assert Post._detect_cta("What do you think?") is True
        assert Post._detect_cta("Comment below") is True
        assert Post._detect_cta("Share this post") is True
        assert Post._detect_cta("No call to action here") is False

    def test_build_system_prompt_called(self, content_generator, sample_client_brief):
        """Test system prompt building is called during generation"""
        with (
            patch.object(content_generator, "_build_system_prompt") as mock_build,
            patch.object(content_generator, "_generate_single_post") as mock_gen_single,
        ):

            mock_build.return_value = "Test system prompt"
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
            )

            # System prompt should be built once and cached
            mock_build.assert_called_once()

    def test_logging_during_generation(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test appropriate logging during generation"""
        with (
            patch.object(content_generator, "_generate_single_post") as mock_gen_single,
            patch("src.agents.content_generator.logger") as mock_logger,
        ):

            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
            )

            # Should log generation start and completion
            assert mock_logger.info.call_count >= 2

    def test_client_memory_integration(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test client memory is used when database available"""
        mock_db = Mock()
        mock_db.get_client_memory.return_value = None
        content_generator.db = mock_db

        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
                use_client_memory=True,
            )

            # Should attempt to get client memory
            mock_db.get_client_memory.assert_called_once_with("Test Company")

    def test_client_memory_disabled(self, content_generator, sample_client_brief):
        """Test client memory not used when disabled"""
        mock_db = Mock()
        content_generator.db = mock_db

        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test",
            )

            content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
                use_client_memory=False,
            )

            # Should NOT call get_client_memory
            mock_db.get_client_memory.assert_not_called()
