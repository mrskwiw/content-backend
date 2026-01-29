"""Unit tests for MemoryLearningAgent"""

from datetime import datetime
from pathlib import Path

import pytest

from src.agents.memory_learning_agent import MemoryLearningAgent
from src.database.project_db import ProjectDatabase
from src.models.client_memory import FeedbackTheme
from src.models.post import Post
from src.models.project import Project, Revision
from src.models.voice_guide import EnhancedVoiceGuide


class TestMemoryLearningAgent:
    """Test MemoryLearningAgent functionality"""

    @pytest.fixture(autouse=True)
    def cleanup_test_data(self):
        """Clean up test data before and after each test"""
        db_path = Path(__file__).parent.parent.parent / "data" / "projects.db"
        db = ProjectDatabase(db_path)

        # Clean up before test
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM template_performance WHERE client_name LIKE "TestClient_%"')
            cursor.execute(
                'DELETE FROM client_feedback_themes WHERE client_name LIKE "TestClient_%"'
            )
            cursor.execute('DELETE FROM client_voice_samples WHERE client_name LIKE "TestClient_%"')
            cursor.execute('DELETE FROM client_history WHERE client_name LIKE "TestClient_%"')
            conn.commit()

        yield

        # Clean up after test
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM template_performance WHERE client_name LIKE "TestClient_%"')
            cursor.execute(
                'DELETE FROM client_feedback_themes WHERE client_name LIKE "TestClient_%"'
            )
            cursor.execute('DELETE FROM client_voice_samples WHERE client_name LIKE "TestClient_%"')
            cursor.execute('DELETE FROM client_history WHERE client_name LIKE "TestClient_%"')
            conn.commit()

    @pytest.fixture
    def db(self):
        """Get database instance"""
        db_path = Path(__file__).parent.parent.parent / "data" / "projects.db"
        return ProjectDatabase(db_path)

    @pytest.fixture
    def agent(self, db):
        """Get learning agent"""
        return MemoryLearningAgent(db)

    @pytest.fixture
    def test_client(self):
        """Test client name"""
        return f"TestClient_Learning_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @pytest.fixture
    def sample_project(self, test_client):
        """Sample project"""
        return Project(
            project_id=f"{test_client}_20251201_120000",
            client_name=test_client,
            num_posts=30,
            deliverable_path=f"data/outputs/{test_client}/deliverable.md",
        )

    @pytest.fixture
    def sample_posts(self, test_client):
        """Sample posts"""
        return [
            Post(
                content="Test post 1",
                template_id=1,
                template_name="Problem Recognition",
                variant=1,
                client_name=test_client,
            ),
            Post(
                content="Test post 2",
                template_id=1,
                template_name="Problem Recognition",
                variant=2,
                client_name=test_client,
            ),
            Post(
                content="Test post 3",
                template_id=6,
                template_name="Personal Story",
                variant=1,
                client_name=test_client,
            ),
        ]

    @pytest.fixture
    def sample_voice_guide(self, test_client):
        """Sample voice guide"""
        from src.models.voice_guide import VoicePattern

        return EnhancedVoiceGuide(
            company_name=test_client,
            generated_from_posts=30,
            dominant_tones=["professional", "friendly"],
            tone_consistency_score=0.85,
            voice_archetype="Expert",
            average_readability_score=72.5,
            average_word_count=220,
            average_paragraph_count=3.5,
            question_usage_rate=0.4,
            common_opening_hooks=[
                VoicePattern(
                    pattern_type="opening",
                    examples=["Ever wonder why...", "Here's the thing..."],
                    frequency=10,
                    description="Curiosity-driven openings",
                )
            ],
            common_transitions=[
                VoicePattern(
                    pattern_type="transition",
                    examples=["The key is...", "But here's what matters..."],
                    frequency=8,
                    description="Authority transitions",
                )
            ],
            common_ctas=[
                VoicePattern(
                    pattern_type="cta",
                    examples=["What's your take?", "Drop a comment..."],
                    frequency=15,
                    description="Engagement-focused CTAs",
                )
            ],
            key_phrases_used=["data-driven", "actionable insights"],
            dos=["Use conversational tone"],
            donts=["Don't be too formal"],
        )

    def test_learn_from_project_creates_memory(
        self, agent, sample_project, sample_posts, test_client
    ):
        """Test that learning from project creates client memory"""
        memory = agent.learn_from_project(sample_project, sample_posts)

        assert memory is not None
        assert memory.client_name == test_client
        assert memory.total_projects == 1
        assert memory.total_posts_generated == 30
        assert memory.is_repeat_client is True

    def test_learn_from_project_with_voice_guide(
        self, agent, sample_project, sample_posts, sample_voice_guide
    ):
        """Test learning with voice guide"""
        memory = agent.learn_from_project(sample_project, sample_posts, sample_voice_guide)

        assert memory.voice_archetype == "Expert"
        assert memory.average_readability_score == 72.5
        assert len(memory.signature_phrases) > 0

    def test_learn_from_template_usage(self, agent, db, sample_project, sample_posts, test_client):
        """Test template usage learning"""
        agent.learn_from_project(sample_project, sample_posts)

        # Check template performance was recorded
        perf = db.get_template_performance(test_client)

        assert 1 in perf  # Template 1 used twice
        assert 6 in perf  # Template 6 used once
        assert perf[1]["usage_count"] == 2
        assert perf[6]["usage_count"] == 1

    def test_extract_feedback_themes_tone(self, agent):
        """Test tone theme extraction"""
        feedback = "Please make this more casual and friendly"
        themes = agent._extract_feedback_themes(feedback)

        assert len(themes) > 0
        tone_themes = [t for t in themes if t.theme_type == "tone"]
        assert len(tone_themes) == 1
        assert tone_themes[0].feedback_phrase == "more casual"

    def test_extract_feedback_themes_length(self, agent):
        """Test length theme extraction"""
        feedback = "This is too long, please make it shorter"
        themes = agent._extract_feedback_themes(feedback)

        length_themes = [t for t in themes if t.theme_type == "length"]
        assert len(length_themes) == 1
        assert length_themes[0].feedback_phrase == "too long"

    def test_extract_feedback_themes_cta(self, agent):
        """Test CTA theme extraction"""
        feedback = "The call to action needs to be stronger"
        themes = agent._extract_feedback_themes(feedback)

        cta_themes = [t for t in themes if t.theme_type == "cta"]
        assert len(cta_themes) == 1
        assert cta_themes[0].feedback_phrase == "stronger cta"

    def test_extract_feedback_themes_data(self, agent):
        """Test data usage theme extraction"""
        feedback = "Can you add more stats and numbers to support the claims?"
        themes = agent._extract_feedback_themes(feedback)

        data_themes = [t for t in themes if t.theme_type == "data_usage"]
        assert len(data_themes) == 1
        assert data_themes[0].feedback_phrase == "add more data"

    def test_extract_feedback_themes_emoji(self, agent):
        """Test emoji theme extraction"""
        feedback = "Please add some emojis to make it more engaging"
        themes = agent._extract_feedback_themes(feedback)

        emoji_themes = [t for t in themes if t.theme_type == "emoji"]
        assert len(emoji_themes) == 1
        assert emoji_themes[0].feedback_phrase == "add emoji"

    def test_extract_feedback_themes_structure(self, agent):
        """Test structure theme extraction"""
        feedback = "The flow could be better. Can you reorganize this?"
        themes = agent._extract_feedback_themes(feedback)

        structure_themes = [t for t in themes if t.theme_type == "structure"]
        assert len(structure_themes) == 1
        assert structure_themes[0].feedback_phrase == "improve structure"

    def test_learn_from_revision(self, agent, db, sample_project, test_client):
        """Test learning from revision"""
        # Create project first
        db.create_project(sample_project)

        # Create revision
        revision = Revision(
            revision_id=f"{sample_project.project_id}_rev_1",
            project_id=sample_project.project_id,
            attempt_number=1,
            feedback="Please make this more casual and shorter",
        )
        db.create_revision(revision)

        # Learn from revision
        memory = agent.learn_from_revision(revision)

        assert memory.total_revisions == 1

        # Check themes were recorded
        themes = db.get_feedback_themes(test_client)
        assert len(themes) >= 2  # tone and length themes

    def test_synthesize_multi_project_learnings_insufficient_projects(self, agent, test_client):
        """Test synthesis with insufficient projects"""
        # Create memory with only 1 project
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Try to synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        # Should return memory unchanged (need 2+ projects)
        assert result.total_projects == 1

    def test_synthesize_multi_project_learnings_with_templates(self, agent, db, test_client):
        """Test synthesis with template performance data"""
        # Create memory with 2+ projects
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Add template performance
        # Template 1: good (2 uses, no revisions)
        db.update_template_performance(test_client, 1, False, 8.5)
        db.update_template_performance(test_client, 1, False, 8.5)

        # Template 6: bad (2 uses, both revised)
        db.update_template_performance(test_client, 6, True, 5.0)
        db.update_template_performance(test_client, 6, True, 5.0)

        # Synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        assert 1 in result.preferred_templates  # Good template
        assert 6 in result.avoided_templates  # Bad template

    def test_synthesize_multi_project_learnings_with_themes(self, agent, db, test_client):
        """Test synthesis with recurring feedback themes"""
        # Create memory with 2+ projects
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Record recurring theme
        theme = FeedbackTheme(theme_type="tone", feedback_phrase="more casual")
        db.record_feedback_theme(test_client, theme)
        db.record_feedback_theme(test_client, theme)  # 2nd occurrence

        # Synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        assert "tone" in result.voice_adjustments
        assert result.voice_adjustments["tone"] == "more casual"

    def test_get_memory_insights(self, agent, db, test_client):
        """Test getting memory insights"""
        # Create memory
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.voice_archetype = "Expert"
        memory.signature_phrases = ["data-driven", "actionable"]
        agent.db.update_client_memory(memory)

        # Get insights
        insights = agent.get_memory_insights(test_client)

        assert insights["client_name"] == test_client
        assert insights["total_projects"] == 1
        assert insights["is_repeat_client"] is True
        assert insights["voice_archetype"] == "Expert"
        assert len(insights["signature_phrases"]) == 2

    def test_get_memory_insights_not_found(self, agent):
        """Test insights for non-existent client"""
        insights = agent.get_memory_insights("NonExistentClient")

        assert "error" in insights
        assert insights["error"] == "Client not found"

    def test_learn_from_revision_project_not_found(self, agent):
        """Test learning from revision when project doesn't exist"""
        revision = Revision(
            revision_id="nonexistent_rev",
            project_id="nonexistent_project",
            attempt_number=1,
            feedback="Some feedback",
        )

        memory = agent.learn_from_revision(revision)

        # Should return default memory with "Unknown" client
        assert memory.client_name == "Unknown"

    def test_learn_from_revision_with_existing_memory(self, agent, db, sample_project, test_client):
        """Test learning from revision with pre-existing memory"""
        db.create_project(sample_project)

        # Create pre-existing memory
        existing_memory = db.get_or_create_client_memory(test_client)
        existing_memory.add_revisions(5)  # Already has 5 revisions
        db.update_client_memory(existing_memory)

        revision = Revision(
            revision_id=f"{sample_project.project_id}_rev_2",
            project_id=sample_project.project_id,
            attempt_number=1,
            feedback="More feedback",
        )
        db.create_revision(revision)

        # Pass existing memory
        memory = agent.learn_from_revision(revision, memory=existing_memory)

        assert memory.total_revisions == 6  # 5 + 1

    def test_extract_feedback_themes_too_short(self, agent):
        """Test length theme extraction for 'too short'"""
        feedback = "This is too short, please add more detail"
        themes = agent._extract_feedback_themes(feedback)

        length_themes = [t for t in themes if t.theme_type == "length"]
        assert len(length_themes) == 1
        assert length_themes[0].feedback_phrase == "too short"

    def test_extract_feedback_themes_remove_cta(self, agent):
        """Test CTA theme extraction for removing CTA"""
        feedback = "Please remove the CTA from this post"
        themes = agent._extract_feedback_themes(feedback)

        cta_themes = [t for t in themes if t.theme_type == "cta"]
        assert len(cta_themes) == 1
        assert cta_themes[0].feedback_phrase == "remove cta"

    def test_extract_feedback_themes_less_data(self, agent):
        """Test data usage theme for less data"""
        feedback = "Too many numbers, please remove some stats"
        themes = agent._extract_feedback_themes(feedback)

        data_themes = [t for t in themes if t.theme_type == "data_usage"]
        assert len(data_themes) == 1
        assert data_themes[0].feedback_phrase == "less data"

    def test_extract_feedback_themes_remove_emoji(self, agent):
        """Test emoji theme for removing emojis"""
        feedback = "No emoji please, it looks unprofessional"
        themes = agent._extract_feedback_themes(feedback)

        emoji_themes = [t for t in themes if t.theme_type == "emoji"]
        assert len(emoji_themes) == 1
        assert emoji_themes[0].feedback_phrase == "remove emoji"

    def test_learn_from_voice_guide_empty_patterns(
        self, agent, sample_project, sample_posts, test_client
    ):
        """Test learning from voice guide with empty patterns"""
        voice_guide = EnhancedVoiceGuide(
            company_name=test_client,
            generated_from_posts=30,
            dominant_tones=["professional"],
            tone_consistency_score=0.85,
            voice_archetype="Expert",
            average_readability_score=70.0,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.3,
            common_opening_hooks=[],  # Empty
            common_transitions=[],  # Empty
            common_ctas=[],  # Empty
            key_phrases_used=[],
            dos=[],
            donts=[],
        )

        memory = agent.learn_from_project(sample_project, sample_posts, voice_guide)

        assert memory.voice_archetype == "Expert"
        assert memory.average_readability_score == 70.0

    def test_learn_from_voice_guide_running_average(
        self, agent, db, sample_project, sample_posts, test_client
    ):
        """Test readability score running average calculation"""
        # First project
        voice_guide1 = EnhancedVoiceGuide(
            company_name=test_client,
            generated_from_posts=30,
            dominant_tones=["professional"],
            tone_consistency_score=0.85,
            voice_archetype="Expert",
            average_readability_score=70.0,
            average_word_count=200,
            average_paragraph_count=3.0,
            question_usage_rate=0.3,
            common_opening_hooks=[],
            common_transitions=[],
            common_ctas=[],
            key_phrases_used=["phrase1", "phrase2"],
            dos=[],
            donts=[],
        )

        memory = agent.learn_from_project(sample_project, sample_posts, voice_guide1)
        assert memory.average_readability_score == 70.0

        # Second project
        project2 = Project(
            project_id=f"{test_client}_20251202_120000",
            client_name=test_client,
            num_posts=30,
            deliverable_path=f"data/outputs/{test_client}/deliverable2.md",
        )

        voice_guide2 = EnhancedVoiceGuide(
            company_name=test_client,
            generated_from_posts=30,
            dominant_tones=["casual"],
            tone_consistency_score=0.80,
            voice_archetype="Storyteller",  # Different, should not override
            average_readability_score=80.0,  # Different - should average
            average_word_count=250,
            average_paragraph_count=4.0,
            question_usage_rate=0.4,
            common_opening_hooks=[],
            common_transitions=[],
            common_ctas=[],
            key_phrases_used=["phrase3", "phrase4"],  # Different phrases
            dos=[],
            donts=[],
        )

        memory = agent.learn_from_project(project2, sample_posts, voice_guide2)

        # Running average: (70 * 1 + 80) / 2 = 75
        assert memory.average_readability_score == 75.0
        # Voice archetype should remain "Expert" (first project)
        assert memory.voice_archetype == "Expert"
        # Signature phrases should have new ones added
        assert len(memory.signature_phrases) >= 2

    def test_synthesize_with_voice_samples_short_posts(self, agent, db, test_client):
        """Test synthesis with voice samples showing short posts"""
        from src.models.client_memory import VoiceSample

        # Create memory with 2+ projects
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Store voice sample with short average word count
        voice_sample = VoiceSample(
            client_name=test_client,
            project_id="proj1",
            average_readability=70.0,
            voice_archetype="Expert",
            dominant_tone="professional",
            average_word_count=150,  # Short
            question_usage_rate=0.3,
            common_hooks=[],
            common_transitions=[],
            common_ctas=[],
            key_phrases=[],
        )
        db.store_voice_sample(voice_sample)

        # Synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        # Should set optimal word count for short posts
        assert result.optimal_word_count_min == 100
        assert result.optimal_word_count_max == 200

    def test_synthesize_with_voice_samples_long_posts(self, agent, db, test_client):
        """Test synthesis with voice samples showing long posts"""
        from src.models.client_memory import VoiceSample

        # Create memory with 2+ projects
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Store voice sample with long average word count
        voice_sample = VoiceSample(
            client_name=test_client,
            project_id="proj1",
            average_readability=70.0,
            voice_archetype="Expert",
            dominant_tone="professional",
            average_word_count=350,  # Long
            question_usage_rate=0.3,
            common_hooks=[],
            common_transitions=[],
            common_ctas=[],
            key_phrases=[],
        )
        db.store_voice_sample(voice_sample)

        # Synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        # Should set optimal word count for long posts
        assert result.optimal_word_count_min == 250
        assert result.optimal_word_count_max == 350

    def test_synthesize_with_voice_samples_medium_posts(self, agent, db, test_client):
        """Test synthesis with voice samples showing medium posts"""
        from src.models.client_memory import VoiceSample

        # Create memory with 2+ projects
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Store voice sample with medium average word count
        voice_sample = VoiceSample(
            client_name=test_client,
            project_id="proj1",
            average_readability=70.0,
            voice_archetype="Expert",
            dominant_tone="professional",
            average_word_count=250,  # Medium
            question_usage_rate=0.3,
            common_hooks=[],
            common_transitions=[],
            common_ctas=[],
            key_phrases=[],
        )
        db.store_voice_sample(voice_sample)

        # Synthesize
        result = agent.synthesize_multi_project_learnings(test_client)

        # Should set optimal word count for medium posts
        assert result.optimal_word_count_min == 150
        assert result.optimal_word_count_max == 250

    def test_get_memory_insights_with_themes_and_templates(self, agent, db, test_client):
        """Test insights with feedback themes and template performance"""
        # Create memory
        memory = agent.db.get_or_create_client_memory(test_client)
        memory.add_project(30, 1800.0)
        agent.db.update_client_memory(memory)

        # Add feedback themes
        theme = FeedbackTheme(theme_type="tone", feedback_phrase="more casual")
        db.record_feedback_theme(test_client, theme)

        # Add template performance
        db.update_template_performance(test_client, 1, False, 8.5)
        db.update_template_performance(test_client, 2, True, 6.0)

        # Get insights
        insights = agent.get_memory_insights(test_client)

        assert "top_feedback_themes" in insights
        assert len(insights["top_feedback_themes"]) >= 1
        assert "best_templates" in insights
        assert len(insights["best_templates"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
