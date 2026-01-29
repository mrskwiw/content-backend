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

            _generator = ContentGeneratorAgent()

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

    def test_repeat_client_with_preferred_templates(
        self, content_generator, sample_client_brief, mock_template_loader
    ):
        """Test repeat client with preferred and avoided templates"""
        from src.models.client_memory import ClientMemory

        # Create repeat client memory with preferences
        mock_memory = ClientMemory(
            client_name="Test Company",
            total_projects=3,
            is_repeat_client=True,
            preferred_templates=[1, 2, 5],
            avoided_templates=[3, 7],
            signature_phrases=["test phrase", "example"],
            voice_adjustments={"tone": "more casual", "length": "shorter"},
            optimal_word_count_min=100,
            optimal_word_count_max=200,
        )

        mock_db = Mock()
        mock_db.get_client_memory.return_value = mock_memory
        content_generator.db = mock_db

        with patch.object(content_generator, "_generate_single_post") as mock_gen_single:
            mock_gen_single.return_value = Post(
                content="Test",
                template_id=1,
                template_name="Test",
                client_name="Test Company",
            )

            result = content_generator.generate_posts(
                client_brief=sample_client_brief,
                num_posts=2,
                use_client_memory=True,
            )

            # Should have generated posts
            assert len(result) == 2
            # Template loader should be called with memory preferences
            mock_template_loader.select_templates_for_client.assert_called_once()
            call_kwargs = mock_template_loader.select_templates_for_client.call_args[1]
            # Uses boost_templates and avoid_templates parameters
            assert call_kwargs["boost_templates"] == [1, 2, 5]
            assert call_kwargs["avoid_templates"] == [3, 7]

    def test_build_system_prompt_with_key_phrases(self, content_generator, sample_client_brief):
        """Test system prompt includes key phrases"""
        sample_client_brief.key_phrases = ["innovation", "transform", "growth"]

        prompt = content_generator._build_system_prompt(
            client_brief=sample_client_brief,
            platform=Platform.LINKEDIN,
        )

        assert "KEY PHRASES TO USE" in prompt
        assert "innovation" in prompt
        assert "transform" in prompt

    def test_build_system_prompt_with_misconceptions(self, content_generator, sample_client_brief):
        """Test system prompt includes misconceptions to address"""
        sample_client_brief.misconceptions = ["Common myth 1", "Industry fallacy"]

        prompt = content_generator._build_system_prompt(
            client_brief=sample_client_brief,
            platform=Platform.LINKEDIN,
        )

        assert "COMMON MISCONCEPTIONS TO ADDRESS" in prompt
        assert "Common myth 1" in prompt

    def test_build_system_prompt_with_client_memory(self, content_generator, sample_client_brief):
        """Test system prompt includes client memory insights"""
        from src.models.client_memory import ClientMemory

        mock_memory = ClientMemory(
            client_name="Test Company",
            total_projects=5,
            is_repeat_client=True,
            voice_adjustments={"tone": "more professional", "style": "concise"},
            signature_phrases=["let's dive in", "here's the truth"],
            optimal_word_count_min=150,
            optimal_word_count_max=250,
        )

        prompt = content_generator._build_system_prompt(
            client_brief=sample_client_brief,
            platform=Platform.LINKEDIN,
            client_memory=mock_memory,
        )

        assert "[CLIENT HISTORY]" in prompt
        assert "repeat client" in prompt
        assert "LEARNED PREFERENCES" in prompt
        assert "SIGNATURE PHRASES" in prompt
        assert "OPTIMAL LENGTH" in prompt
        assert "150-250 words" in prompt

    def test_build_skill_guidance_no_skill(self, mock_anthropic_client, mock_template_loader):
        """Test skill guidance returns empty when skill not loaded"""
        # Create generator with skill disabled
        generator = ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
            use_content_skill=False,
        )

        guidance = generator._build_skill_guidance(Platform.LINKEDIN)
        assert guidance == ""

    def test_content_skill_loading_failure(self, mock_anthropic_client, mock_template_loader):
        """Test graceful handling when skill loading fails"""
        with patch("src.agents.content_generator.load_skill") as mock_load:
            mock_load.side_effect = Exception("Skill not found")

            generator = ContentGeneratorAgent(
                client=mock_anthropic_client,
                template_loader=mock_template_loader,
                use_content_skill=True,
            )

            # Should not raise, just log warning
            assert generator.content_skill is None


class TestGenerateWithVoiceSamples:
    """Tests for voice sample integration"""

    @pytest.fixture
    def content_generator_with_db(self, mock_anthropic_client, mock_template_loader):
        """Content generator with mocked database"""

        generator = ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
            use_content_skill=False,
        )
        generator.db = Mock()
        return generator

    @pytest.fixture
    def sample_client_brief(self):
        """Sample client brief"""
        return ClientBrief(
            company_name="Voice Test Company",
            business_description="Test business",
            ideal_customer="Test customers",
            main_problem_solved="Test problem",
        )

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        return Mock()

    @pytest.fixture
    def mock_template_loader(self):
        """Mock template loader"""
        loader = Mock()
        loader.select_templates_for_client.return_value = [
            Template(
                template_id=1,
                name="Template 1",
                structure="Test structure",
                template_type=TemplateType.PROBLEM_RECOGNITION,
                difficulty=TemplateDifficulty.FAST,
                best_for="Test",
            )
        ]
        return loader

    @pytest.mark.asyncio
    async def test_generate_posts_with_voice_matching_async_no_db(
        self, mock_anthropic_client, mock_template_loader, sample_client_brief
    ):
        """Test voice sample generation without database returns None report"""
        generator = ContentGeneratorAgent(
            client=mock_anthropic_client,
            template_loader=mock_template_loader,
            use_content_skill=False,
        )
        generator.db = None

        with patch.object(generator, "generate_posts_async") as mock_async:
            mock_async.return_value = [
                Post(content="Test", template_id=1, template_name="Test", client_name="Test")
            ]

            posts, report = await generator.generate_posts_with_voice_matching_async(
                client_brief=sample_client_brief,
                num_posts=1,
            )

            assert posts is not None
            assert report is None

    @pytest.mark.asyncio
    async def test_generate_posts_with_voice_matching_async_no_samples_in_db(
        self, content_generator_with_db, sample_client_brief
    ):
        """Test voice sample generation when no samples exist"""
        content_generator_with_db.db.get_voice_sample_upload_stats.return_value = None

        with patch.object(content_generator_with_db, "generate_posts_async") as mock_async:
            mock_async.return_value = [
                Post(content="Test", template_id=1, template_name="Test", client_name="Test")
            ]

            posts, report = (
                await content_generator_with_db.generate_posts_with_voice_matching_async(
                    client_brief=sample_client_brief,
                    num_posts=1,
                )
            )

            assert posts is not None
            assert report is None

    @pytest.mark.asyncio
    async def test_generate_posts_with_voice_matching_async_stats_but_no_samples(
        self, content_generator_with_db, sample_client_brief
    ):
        """Test when stats exist but samples can't be retrieved"""
        content_generator_with_db.db.get_voice_sample_upload_stats.return_value = {
            "sample_count": 5,
            "total_words": 1000,
        }
        content_generator_with_db.db.get_voice_sample_uploads.return_value = []

        with patch.object(content_generator_with_db, "generate_posts_async") as mock_async:
            mock_async.return_value = [
                Post(content="Test", template_id=1, template_name="Test", client_name="Test")
            ]

            posts, report = (
                await content_generator_with_db.generate_posts_with_voice_matching_async(
                    client_brief=sample_client_brief,
                    num_posts=1,
                )
            )

            assert posts is not None
            assert report is None

    @pytest.mark.asyncio
    async def test_generate_posts_with_voice_matching_async_full_flow(
        self, content_generator_with_db, sample_client_brief
    ):
        """Test full voice sample generation flow"""
        # Use Mock objects for voice samples to avoid validation constraints
        mock_sample_1 = Mock()
        mock_sample_1.sample_text = (
            "This is a test voice sample with professional tone and business language."
        )
        mock_sample_1.sample_source = "linkedin"

        mock_sample_2 = Mock()
        mock_sample_2.sample_text = (
            "Another sample showing consistent voice patterns in professional context."
        )
        mock_sample_2.sample_source = "linkedin"

        voice_samples = [mock_sample_1, mock_sample_2]

        content_generator_with_db.db.get_voice_sample_upload_stats.return_value = {
            "sample_count": 2,
            "total_words": 200,
        }
        content_generator_with_db.db.get_voice_sample_uploads.return_value = voice_samples

        # Mock voice analyzer - create a Mock instead of real VoiceGuide
        mock_voice_guide = Mock()
        mock_voice_guide.voice_archetype = "The Professional"
        mock_voice_guide.average_readability_score = 65.0
        mock_voice_guide.average_word_count = 150
        mock_voice_guide.key_phrases_used = ["test phrase", "example"]

        with (
            patch.object(content_generator_with_db, "generate_posts_async") as mock_async,
            patch("src.agents.voice_analyzer.VoiceAnalyzer") as mock_analyzer_class,
            patch("src.utils.voice_matcher.VoiceMatcher") as mock_matcher_class,
        ):
            mock_async.return_value = [
                Post(
                    content="Generated test post",
                    template_id=1,
                    template_name="Test",
                    client_name="Voice Test Company",
                )
            ]

            # Mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.analyze_voice_samples.return_value = mock_voice_guide
            mock_analyzer_class.return_value = mock_analyzer

            # Mock matcher
            mock_match_report = Mock()
            mock_match_report.match_score = 0.85
            mock_match_report.readability_score = Mock(score=0.9)
            mock_match_report.word_count_score = Mock(score=0.8)
            mock_match_report.archetype_score = Mock(score=0.85)
            mock_match_report.phrase_usage_score = Mock(score=0.75)

            mock_matcher = Mock()
            mock_matcher.calculate_match_score.return_value = mock_match_report
            mock_matcher_class.return_value = mock_matcher

            posts, report = (
                await content_generator_with_db.generate_posts_with_voice_matching_async(
                    client_brief=sample_client_brief,
                    num_posts=1,
                )
            )

            assert posts is not None
            assert len(posts) == 1
            assert report is not None
            assert report.match_score == 0.85

    @pytest.mark.asyncio
    async def test_generate_posts_with_voice_matching_async_matcher_error(
        self, content_generator_with_db, sample_client_brief
    ):
        """Test graceful handling when voice matcher fails"""
        # Use Mock objects to avoid validation constraints
        mock_sample = Mock()
        mock_sample.sample_text = "Test sample text for voice analysis"
        mock_sample.sample_source = "linkedin"

        voice_samples = [mock_sample]

        content_generator_with_db.db.get_voice_sample_upload_stats.return_value = {
            "sample_count": 1,
            "total_words": 100,
        }
        content_generator_with_db.db.get_voice_sample_uploads.return_value = voice_samples

        mock_voice_guide = Mock()
        mock_voice_guide.average_readability_score = 60.0
        mock_voice_guide.voice_archetype = None
        mock_voice_guide.average_word_count = None
        mock_voice_guide.key_phrases_used = []

        with (
            patch.object(content_generator_with_db, "generate_posts_async") as mock_async,
            patch("src.agents.voice_analyzer.VoiceAnalyzer") as mock_analyzer_class,
            patch("src.utils.voice_matcher.VoiceMatcher") as mock_matcher_class,
        ):
            mock_async.return_value = [
                Post(content="Test", template_id=1, template_name="Test", client_name="Test")
            ]

            mock_analyzer = Mock()
            mock_analyzer.analyze_voice_samples.return_value = mock_voice_guide
            mock_analyzer_class.return_value = mock_analyzer

            # Make matcher raise exception
            mock_matcher = Mock()
            mock_matcher.calculate_match_score.side_effect = Exception("Matcher error")
            mock_matcher_class.return_value = mock_matcher

            posts, report = (
                await content_generator_with_db.generate_posts_with_voice_matching_async(
                    client_brief=sample_client_brief,
                    num_posts=1,
                )
            )

            # Should return posts but None report on error
            assert posts is not None
            assert report is None
