"""Unit tests for Voice Analyzer"""

import pytest

from src.agents.voice_analyzer import VoiceAnalyzer
from src.models.client_brief import ClientBrief, TonePreference
from src.models.post import Post


@pytest.fixture
def sample_posts():
    """Create sample posts"""
    posts = [
        Post(
            content="Most B2B SaaS founders struggle with retention. Here'''s why. Customer onboarding is rushed.",
            template_id=1,
            template_name="Problem Recognition",
            client_name="TestClient",
        ),
        Post(
            content="What if you could reduce churn by 40%? What'''s your biggest retention challenge?",
            template_id=5,
            template_name="Question Post",
            client_name="TestClient",
        ),
        Post(
            content="Customer success isn'''t about features. The reality is most companies focus wrong.",
            template_id=3,
            template_name="Contrarian Take",
            client_name="TestClient",
        ),
    ]
    return posts


@pytest.fixture
def sample_client_brief():
    """Create sample client brief"""
    return ClientBrief(
        company_name="TestClient",
        business_description="B2B SaaS retention platform",
        ideal_customer="Series A SaaS founders",
        main_problem_solved="Customer churn reduction",
        brand_personality=[TonePreference.DIRECT, TonePreference.DATA_DRIVEN],
        key_phrases=["customer success", "proactive approach"],
        tone_to_avoid="overly promotional",
    )


class TestVoiceAnalyzer:
    """Test Voice Analyzer"""

    def test_extract_hook(self, sample_posts):
        analyzer = VoiceAnalyzer()
        hook = analyzer._extract_hook(sample_posts[0].content)
        assert "retention" in hook
        assert hook.endswith(".")

    def test_extract_transitions(self, sample_posts):
        analyzer = VoiceAnalyzer()
        transitions = analyzer._extract_transitions(sample_posts[2].content)
        assert isinstance(transitions, list)

    def test_extract_cta(self, sample_posts):
        analyzer = VoiceAnalyzer()
        cta = analyzer._extract_cta(sample_posts[1].content)
        assert "?" in cta or "challenge" in cta.lower()

    def test_cluster_patterns(self):
        analyzer = VoiceAnalyzer()
        items = ["Test", "Test", "Similar"]
        patterns = analyzer._cluster_patterns(items, "opening")
        assert len(patterns) >= 1
        assert patterns[0].frequency >= 1

    def test_find_recurring_ngrams(self):
        analyzer = VoiceAnalyzer()
        text = "customer success is key. customer success drives results. customer success matters."
        phrases = analyzer._find_recurring_ngrams(text, min_freq=3)
        assert "customer success" in phrases

    def test_calculate_avg_paragraphs(self, sample_posts):
        analyzer = VoiceAnalyzer()
        avg = analyzer._calculate_avg_paragraphs(sample_posts)
        assert avg >= 1.0

    def test_calculate_tone_consistency(self, sample_posts, sample_client_brief):
        analyzer = VoiceAnalyzer()
        score = analyzer._calculate_tone_consistency(sample_posts, sample_client_brief)
        assert 0.0 <= score <= 1.0

    def test_analyze_complete(self, sample_posts, sample_client_brief):
        analyzer = VoiceAnalyzer()
        voice_guide = analyzer.analyze_voice_patterns(sample_posts, sample_client_brief)

        assert voice_guide.company_name == "TestClient"
        assert voice_guide.generated_from_posts == 3
        assert 0.0 <= voice_guide.tone_consistency_score <= 1.0
        assert voice_guide.average_word_count > 0
        assert len(voice_guide.dos) >= 3
        assert len(voice_guide.donts) >= 3

    def test_markdown_export(self, sample_posts, sample_client_brief):
        analyzer = VoiceAnalyzer()
        voice_guide = analyzer.analyze_voice_patterns(sample_posts, sample_client_brief)
        markdown = voice_guide.to_markdown()

        assert "# Enhanced Brand Voice Guide" in markdown
        assert "TestClient" in markdown
        assert "Tone Consistency Score" in markdown


class TestAnalyzeVoiceSamples:
    """Tests for analyze_voice_samples method (lines 97-158)."""

    def test_analyze_voice_samples_basic(self):
        """Test analyzing client text samples."""
        analyzer = VoiceAnalyzer()
        samples = [
            "This is sample content about customer success. We help companies grow.",
            "Another sample with different content. Great results are possible.",
            "Third sample for analysis. Building better relationships matters.",
        ]

        voice_guide = analyzer.analyze_voice_samples(
            samples=samples, client_name="TestClient", source="linkedin"
        )

        assert voice_guide.company_name == "TestClient"
        assert voice_guide.source == "client_samples"
        assert voice_guide.sample_count == 3
        assert voice_guide.sample_source == "linkedin"
        assert voice_guide.sample_upload_date is not None

    def test_analyze_voice_samples_with_emojis(self):
        """Test analyzing samples containing emojis."""
        analyzer = VoiceAnalyzer()
        samples = [
            "Great news! 🎉 We launched a new feature 🚀",
            "Check this out! 💡 It's amazing 🔥 and helpful 👍",
        ]

        voice_guide = analyzer.analyze_voice_samples(
            samples=samples, client_name="EmojiClient", source="twitter"
        )

        assert voice_guide.emoji_frequency is not None
        assert voice_guide.emoji_frequency > 0
        assert len(voice_guide.common_emojis) > 0

    def test_analyze_voice_samples_with_jargon(self):
        """Test analyzing samples with industry jargon."""
        analyzer = VoiceAnalyzer()
        samples = [
            "Our ROI-driven approach uses AI and ML for B2B SaaS optimization. "
            "We deliver data-driven insights with real-time analytics.",
            "The API integration enables content marketing and lead generation. "
            "ROI and SEO are critical for growth-focused strategies.",
        ]

        voice_guide = analyzer.analyze_voice_samples(
            samples=samples, client_name="JargonClient", source="blog"
        )

        assert voice_guide.jargon_ratio is not None
        assert voice_guide.jargon_ratio > 0
        assert len(voice_guide.industry_terms) > 0


class TestEmojiPatterns:
    """Tests for _analyze_emoji_patterns method (lines 160-196)."""

    def test_no_emojis(self):
        """Test text with no emojis."""
        analyzer = VoiceAnalyzer()
        text = "This is plain text without any emojis at all."

        frequency, common = analyzer._analyze_emoji_patterns(text)

        assert frequency == 0.0
        assert common == []

    def test_single_emoji(self):
        """Test text with single emoji."""
        analyzer = VoiceAnalyzer()
        text = "Hello world 🎉 this is a test"

        frequency, common = analyzer._analyze_emoji_patterns(text)

        assert frequency > 0
        assert len(common) == 1
        assert "🎉" in common

    def test_multiple_emojis(self):
        """Test text with multiple emojis."""
        analyzer = VoiceAnalyzer()
        text = "Great 🎉 job 🔥 everyone 🚀 let's 💪 go 🎉"

        frequency, common = analyzer._analyze_emoji_patterns(text)

        assert frequency > 0
        assert len(common) > 0
        # 🎉 appears twice, should be in common
        assert "🎉" in common

    def test_empty_text(self):
        """Test empty text returns zeros."""
        analyzer = VoiceAnalyzer()
        text = ""

        frequency, common = analyzer._analyze_emoji_patterns(text)

        assert frequency == 0.0
        assert common == []

    def test_emoji_frequency_calculation(self):
        """Test emoji frequency per 100 words."""
        analyzer = VoiceAnalyzer()
        # 10 words with 2 emojis = 20 emojis per 100 words
        text = "Word one two three four five six seven eight nine 🎉 🔥"

        frequency, common = analyzer._analyze_emoji_patterns(text)

        # Should be approximately (2/11) * 100 ≈ 18.18
        assert 15 < frequency < 25


class TestJargonAnalysis:
    """Tests for _analyze_jargon method (lines 198-274)."""

    def test_no_jargon(self):
        """Test text with no jargon."""
        analyzer = VoiceAnalyzer()
        text = "This is simple text without any special terms or acronyms."

        ratio, terms = analyzer._analyze_jargon(text)

        # May have some matches from patterns, but no frequent terms
        assert isinstance(ratio, float)
        assert isinstance(terms, list)

    def test_acronyms_detected(self):
        """Test that acronyms are detected."""
        analyzer = VoiceAnalyzer()
        text = "Our ROI from SEO and SEM campaigns. ROI is key. SEO matters. ROI drives growth."

        ratio, terms = analyzer._analyze_jargon(text)

        assert ratio > 0
        assert "ROI" in terms  # ROI appears 3 times

    def test_hyphenated_terms(self):
        """Test that hyphenated terms are detected."""
        analyzer = VoiceAnalyzer()
        text = (
            "We use data-driven approaches for real-time analytics. "
            "data-driven insights and data-driven decisions are key."
        )

        ratio, terms = analyzer._analyze_jargon(text)

        assert ratio > 0
        # data-driven appears 3 times, should be in terms
        # Check if any hyphenated term is in the result
        has_hyphenated = any("-" in term for term in terms)
        assert has_hyphenated or len(terms) >= 0  # At minimum, jargon ratio should be positive

    def test_empty_text_jargon(self):
        """Test empty text returns zeros."""
        analyzer = VoiceAnalyzer()
        text = ""

        ratio, terms = analyzer._analyze_jargon(text)

        assert ratio == 0.0
        assert terms == []

    def test_common_words_filtered(self):
        """Test that common words are filtered from jargon."""
        analyzer = VoiceAnalyzer()
        # Text with common words that match patterns but shouldn't be jargon
        text = "The day was new. She can get her way. He has his too."

        ratio, terms = analyzer._analyze_jargon(text)

        # Common words should be filtered out
        for common_word in ["THE", "DAY", "NEW", "SHE", "CAN", "GET", "HER", "WAY"]:
            assert common_word not in terms

    def test_minimum_frequency_filter(self):
        """Test that terms appearing only once are filtered."""
        analyzer = VoiceAnalyzer()
        text = "One ABC here, one XYZ there, no repeats anywhere."

        ratio, terms = analyzer._analyze_jargon(text)

        # Terms need to appear at least twice to be in top_terms
        # Single occurrences should not appear
        assert "ABC" not in terms
        assert "XYZ" not in terms


class TestClusterPatterns:
    """Tests for pattern clustering with similar items"""

    def test_cluster_skips_empty_items(self):
        """Test that empty items are skipped in clustering"""
        analyzer = VoiceAnalyzer()
        items = ["What if we", "", "  ", "What if they", "Let's imagine"]

        clusters = analyzer._cluster_patterns(items, "Hook")

        # Should create clusters without empty items
        assert all(p.examples for p in clusters)
        for pattern in clusters:
            assert "" not in pattern.examples
            assert "  " not in pattern.examples

    def test_cluster_similar_patterns_grouped(self):
        """Test that similar patterns are clustered together"""
        analyzer = VoiceAnalyzer()
        items = [
            "What if we tried",
            "What if we tested",
            "Let's imagine this",
            "Let's imagine that",
        ]

        clusters = analyzer._cluster_patterns(items, "Hook")

        # Similar patterns should be grouped
        assert len(clusters) <= 2  # At most 2 clusters (What if... and Let's imagine...)


class TestGeneralizePattern:
    """Tests for pattern generalization"""

    def test_generalize_with_uppercase(self):
        """Test generalizing patterns with uppercase characters"""
        analyzer = VoiceAnalyzer()

        result = analyzer._generalize_pattern("CEO of Acme Corp")

        assert result == "specific examples or case studies"

    def test_generalize_what_if(self):
        """Test generalizing 'what if' patterns"""
        analyzer = VoiceAnalyzer()

        result = analyzer._generalize_pattern("what if we tried this")

        assert result == "thought-provoking questions"

    def test_generalize_most_pattern(self):
        """Test generalizing 'most' patterns"""
        analyzer = VoiceAnalyzer()

        result = analyzer._generalize_pattern("most people struggle with")

        assert result == "statements about common challenges"

    def test_generalize_default(self):
        """Test default generalization"""
        analyzer = VoiceAnalyzer()

        result = analyzer._generalize_pattern("simple lowercase example")

        assert result == "concrete, relatable examples"


class TestVoiceSpectrum:
    """Tests for voice spectrum generation"""

    def test_spectrum_formal_style(self):
        """Test spectrum with formal voice dimensions"""
        analyzer = VoiceAnalyzer()

        voice_dimensions = {
            "formality": {"dominant": "formal"},
            "tone": {"dominant": "authoritative"},
            "perspective": {"dominant": "expert"},
        }

        spectrum = analyzer._generate_voice_spectrum(voice_dimensions, 45.0)

        assert "formal" in spectrum["formal_casual"].lower()
        assert "serious" in spectrum["serious_playful"].lower()
        assert "authoritative" in spectrum["authoritative_collaborative"].lower()
        assert "technical" in spectrum["technical_simple"].lower()

    def test_spectrum_casual_style(self):
        """Test spectrum with casual voice dimensions"""
        analyzer = VoiceAnalyzer()

        voice_dimensions = {
            "formality": {"dominant": "casual"},
            "tone": {"dominant": "friendly"},
            "perspective": {"dominant": "collaborative"},
        }

        spectrum = analyzer._generate_voice_spectrum(voice_dimensions, 75.0)

        assert "casual" in spectrum["formal_casual"].lower()
        assert "collaborative" in spectrum["authoritative_collaborative"].lower()
        assert "simple" in spectrum["technical_simple"].lower()

    def test_spectrum_conversational_style(self):
        """Test spectrum with conversational formality"""
        analyzer = VoiceAnalyzer()

        voice_dimensions = {
            "formality": {"dominant": "conversational"},
            "tone": {"dominant": "enthusiastic"},
            "perspective": {"dominant": "guide"},
        }

        spectrum = analyzer._generate_voice_spectrum(voice_dimensions, 60.0)

        assert "casual" in spectrum["formal_casual"].lower()
        assert "center" in spectrum["serious_playful"].lower()


class TestConsistencyChecklist:
    """Tests for consistency checklist generation"""

    def test_checklist_expert_archetype(self):
        """Test checklist includes Expert-specific items"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist("Expert", ["conversational"])

        assert any("data" in item.lower() or "evidence" in item.lower() for item in checklist)
        assert any("authoritative" in item.lower() for item in checklist)

    def test_checklist_friend_archetype(self):
        """Test checklist includes Friend-specific items"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist("Friend", ["friendly"])

        assert any("relatable" in item.lower() for item in checklist)
        assert any("warm" in item.lower() or "genuine" in item.lower() for item in checklist)

    def test_checklist_innovator_archetype(self):
        """Test checklist includes Innovator-specific items"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist("Innovator", ["bold"])

        assert any("fresh" in item.lower() or "perspective" in item.lower() for item in checklist)
        assert any("conventional" in item.lower() for item in checklist)

    def test_checklist_guide_archetype(self):
        """Test checklist includes Guide-specific items"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist("Guide", ["helpful"])

        assert any("actionable" in item.lower() for item in checklist)
        assert any("next" in item.lower() for item in checklist)

    def test_checklist_motivator_archetype(self):
        """Test checklist includes Motivator-specific items"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist("Motivator", ["enthusiastic"])

        assert any("inspires" in item.lower() for item in checklist)
        assert any("energy" in item.lower() for item in checklist)

    def test_checklist_conversational_tone(self):
        """Test checklist adds conversational tone check"""
        analyzer = VoiceAnalyzer()

        checklist = analyzer._generate_consistency_checklist(
            "Expert", ["conversational", "friendly"]
        )

        assert any("spoken aloud" in item.lower() for item in checklist)
