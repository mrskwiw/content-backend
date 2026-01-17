"""Unit tests for voice_guide module.

Tests cover:
- EnhancedVoiceGuide model
- to_markdown method with various configurations
- VoicePattern model
"""

import pytest

from src.models.voice_guide import EnhancedVoiceGuide, VoicePattern


class TestVoicePattern:
    """Tests for VoicePattern model."""

    def test_voice_pattern_creation(self):
        """Test basic VoicePattern creation."""
        pattern = VoicePattern(
            pattern_type="opening",
            examples=["Example 1", "Example 2"],
            frequency=5,
            description="Question opener",
        )

        assert pattern.pattern_type == "opening"
        assert len(pattern.examples) == 2
        assert pattern.frequency == 5
        assert pattern.description == "Question opener"

    def test_voice_pattern_frequency_validation(self):
        """Test that frequency must be >= 0."""
        pattern = VoicePattern(
            pattern_type="cta",
            examples=["Test"],
            frequency=0,  # Edge case: exactly 0
            description="Test description",
        )
        assert pattern.frequency == 0


class TestEnhancedVoiceGuideBasic:
    """Tests for EnhancedVoiceGuide basic functionality."""

    @pytest.fixture
    def basic_guide(self):
        """Create a minimal voice guide."""
        return EnhancedVoiceGuide(
            company_name="Test Company",
            generated_from_posts=10,
            tone_consistency_score=0.85,
            average_word_count=200,
            average_paragraph_count=3.5,
            question_usage_rate=0.6,
        )

    def test_basic_guide_creation(self, basic_guide):
        """Test creating a basic voice guide."""
        assert basic_guide.company_name == "Test Company"
        assert basic_guide.generated_from_posts == 10
        assert basic_guide.tone_consistency_score == 0.85
        assert basic_guide.generated_at is not None

    def test_guide_with_optional_fields(self):
        """Test guide with all optional fields populated."""
        guide = EnhancedVoiceGuide(
            company_name="Full Company",
            generated_from_posts=30,
            tone_consistency_score=0.9,
            average_word_count=220,
            average_paragraph_count=4.0,
            question_usage_rate=0.7,
            dominant_tones=["professional", "friendly"],
            average_readability_score=75.5,
            voice_dimensions={
                "formality": {"dominant": "casual"},
                "tone": {"dominant": "friendly"},
                "perspective": {"dominant": "first_person"},
            },
            sentence_variety="high",
            voice_archetype="Friend",
            source="client_samples",
            sample_count=5,
            sample_source="linkedin",
            emoji_frequency=1.5,
            common_emojis=["🚀", "✅", "💡"],
            jargon_ratio=0.15,
            industry_terms=["SaaS", "API", "KPI"],
        )

        assert guide.average_readability_score == 75.5
        assert guide.voice_archetype == "Friend"
        assert len(guide.common_emojis) == 3
        assert guide.jargon_ratio == 0.15


class TestToMarkdownBasic:
    """Tests for to_markdown method - basic output."""

    def test_to_markdown_header(self):
        """Test markdown header section."""
        guide = EnhancedVoiceGuide(
            company_name="Test Co",
            generated_from_posts=15,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "# Enhanced Brand Voice Guide: Test Co" in markdown
        assert "15 posts" in markdown

    def test_to_markdown_dominant_tones(self):
        """Test markdown with dominant tones."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.75,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            dominant_tones=["professional", "authoritative"],
        )

        markdown = guide.to_markdown()

        assert "**Dominant Tones:** Professional, Authoritative" in markdown

    def test_to_markdown_high_consistency_score(self):
        """Test checkmark for high consistency score (>= 70%)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.85,  # 85% >= 70%
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "85% ✓" in markdown

    def test_to_markdown_low_consistency_score(self):
        """Test tilde for low consistency score (< 70%)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.65,  # 65% < 70%
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "65% ~" in markdown


class TestToMarkdownVoiceMetrics:
    """Tests for to_markdown voice metrics section."""

    def test_voice_metrics_with_archetype(self):
        """Test voice metrics section with archetype."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            voice_archetype="Expert",
        )

        markdown = guide.to_markdown()

        assert "### Voice Metrics" in markdown
        assert "**Brand Archetype:** Expert" in markdown

    def test_readability_very_easy(self):
        """Test readability score >= 80 (Very Easy)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            average_readability_score=85.0,
        )

        markdown = guide.to_markdown()

        assert "Very Easy - 6th grade" in markdown

    def test_readability_fairly_easy(self):
        """Test readability score 70-79 (Fairly Easy)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            average_readability_score=75.0,
        )

        markdown = guide.to_markdown()

        assert "Fairly Easy - 7th grade" in markdown

    def test_readability_standard(self):
        """Test readability score 60-69 (Standard)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            average_readability_score=65.0,
        )

        markdown = guide.to_markdown()

        assert "Standard - 8th-9th grade" in markdown

    def test_readability_fairly_difficult(self):
        """Test readability score 50-59 (Fairly Difficult)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            average_readability_score=55.0,
        )

        markdown = guide.to_markdown()

        assert "Fairly Difficult - High school" in markdown

    def test_readability_difficult(self):
        """Test readability score < 50 (Difficult)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            average_readability_score=45.0,
        )

        markdown = guide.to_markdown()

        assert "Difficult - College level" in markdown

    def test_sentence_variety_low(self):
        """Test sentence variety low."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            voice_archetype="Test",  # Needed to show metrics section
            sentence_variety="low",
        )

        markdown = guide.to_markdown()

        assert "**Sentence Variety:** Low 📉" in markdown

    def test_sentence_variety_medium(self):
        """Test sentence variety medium."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            voice_archetype="Test",
            sentence_variety="medium",
        )

        markdown = guide.to_markdown()

        assert "**Sentence Variety:** Medium 📊" in markdown

    def test_sentence_variety_high(self):
        """Test sentence variety high."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            voice_archetype="Test",
            sentence_variety="high",
        )

        markdown = guide.to_markdown()

        assert "**Sentence Variety:** High 📈" in markdown

    def test_voice_dimensions(self):
        """Test voice dimensions display."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            voice_archetype="Guide",
            voice_dimensions={
                "formality": {"dominant": "casual"},
                "tone": {"dominant": "friendly"},
                "perspective": {"dominant": "first_person"},
            },
        )

        markdown = guide.to_markdown()

        assert "**Voice Dimensions:**" in markdown
        assert "Formality: Casual" in markdown
        assert "Tone: Friendly" in markdown
        assert "Perspective: First_Person" in markdown


class TestToMarkdownPatterns:
    """Tests for to_markdown pattern sections."""

    def test_opening_hooks(self):
        """Test opening hooks section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            common_opening_hooks=[
                VoicePattern(
                    pattern_type="opening",
                    examples=["Did you know that...", "Ever wondered why..."],
                    frequency=8,
                    description="Question hook",
                )
            ],
        )

        markdown = guide.to_markdown()

        assert "## Opening Hooks" in markdown
        assert "**Question hook**" in markdown
        assert "appears 8 times" in markdown
        assert "Did you know that..." in markdown

    def test_common_transitions(self):
        """Test common transitions section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            common_transitions=[
                VoicePattern(
                    pattern_type="transition",
                    examples=["Here's the thing:", "But wait, there's more"],
                    frequency=5,
                    description="Attention grabber",
                )
            ],
        )

        markdown = guide.to_markdown()

        assert "## Common Transitions" in markdown
        assert "Here's the thing:" in markdown
        assert "5 times" in markdown
        assert "**Pattern:** Attention grabber" in markdown

    def test_cta_with_questions(self):
        """Test CTA patterns with question CTAs."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            common_ctas=[
                VoicePattern(
                    pattern_type="cta",
                    examples=["What do you think?", "Have you tried this?"],
                    frequency=6,
                    description="Engagement question",
                ),
                VoicePattern(
                    pattern_type="cta",
                    examples=["Learn more", "Click here"],
                    frequency=4,
                    description="Direct action",
                ),
            ],
        )

        markdown = guide.to_markdown()

        assert "## Call-to-Action Patterns" in markdown
        assert "**Open-ended questions**" in markdown
        assert "6 posts" in markdown
        assert "**Direct action**" in markdown
        assert "4 posts" in markdown

    def test_cta_without_questions(self):
        """Test CTA patterns without question CTAs."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            common_ctas=[
                VoicePattern(
                    pattern_type="cta",
                    examples=["Sign up now", "Try it free"],
                    frequency=7,
                    description="Direct call to action",
                )
            ],
        )

        markdown = guide.to_markdown()

        assert "## Call-to-Action Patterns" in markdown
        assert "**Direct call to action**" in markdown
        assert "7 posts" in markdown

    def test_key_phrases(self):
        """Test key phrases section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            key_phrases_used=["game changer", "bottom line", "at the end of the day"],
        )

        markdown = guide.to_markdown()

        assert "## Key Phrases (Used 3+ Times)" in markdown
        assert '"game changer"' in markdown
        assert '"bottom line"' in markdown


class TestToMarkdownStructure:
    """Tests for to_markdown structural patterns section."""

    def test_mid_length_posts_insight(self):
        """Test insight for mid-length posts (200-250 words)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=225,  # Between 200 and 250
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "You favor mid-length posts (200-250 words)" in markdown

    def test_concise_posts_insight(self):
        """Test insight for concise posts (<200 words)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=150,  # < 200
            average_paragraph_count=2.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "You write concise posts (<200 words)" in markdown

    def test_detailed_posts_insight(self):
        """Test insight for detailed posts (>250 words)."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=300,  # > 250
            average_paragraph_count=5.0,
            question_usage_rate=0.5,
        )

        markdown = guide.to_markdown()

        assert "You write detailed posts (>250 words)" in markdown


class TestToMarkdownGuidelines:
    """Tests for to_markdown guidelines section."""

    def test_dos_section(self):
        """Test DO recommendations section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            dos=["Use active voice", "Include statistics", "Ask questions"],
        )

        markdown = guide.to_markdown()

        assert "### ✅ DO:" in markdown
        assert "- Use active voice" in markdown
        assert "- Include statistics" in markdown
        assert "- Ask questions" in markdown

    def test_donts_section(self):
        """Test DON'T recommendations section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            donts=["Use jargon", "Write long paragraphs", "Be overly formal"],
        )

        markdown = guide.to_markdown()

        assert "### ❌ DON'T:" in markdown
        assert "- Use jargon" in markdown
        assert "- Write long paragraphs" in markdown

    def test_examples_section(self):
        """Test strong examples section."""
        guide = EnhancedVoiceGuide(
            company_name="Test",
            generated_from_posts=10,
            tone_consistency_score=0.8,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.5,
            examples=["This is a great opening hook that captures attention."],
        )

        markdown = guide.to_markdown()

        assert "## Strong Examples" in markdown
        assert "**Example:**" in markdown
        assert "> This is a great opening hook" in markdown


class TestToMarkdownEmptyFields:
    """Tests for to_markdown with empty optional fields."""

    def test_no_optional_sections(self):
        """Test markdown with no optional fields populated."""
        guide = EnhancedVoiceGuide(
            company_name="Minimal Co",
            generated_from_posts=5,
            tone_consistency_score=0.7,
            average_word_count=180,
            average_paragraph_count=2.5,
            question_usage_rate=0.3,
            # All optional fields default to empty/None
        )

        markdown = guide.to_markdown()

        # Should still have basic sections
        assert "# Enhanced Brand Voice Guide: Minimal Co" in markdown
        assert "## Structural Patterns" in markdown
        assert "## Writing Guidelines" in markdown

        # Should not have sections that require data
        assert "## Opening Hooks" not in markdown
        assert "## Common Transitions" not in markdown
        assert "## Call-to-Action Patterns" not in markdown
        assert "## Key Phrases" not in markdown
        assert "### Voice Metrics" not in markdown
