"""
Story models for Story Mining feature.

Tracks mined client stories and their usage across posts/platforms.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class MinedStory(Base):
    """
    Mined client stories from Story Mining research tool.

    Stories are valuable content assets that can be reused across posts,
    but should not be repeated on the same platform to avoid redundancy.
    """

    __tablename__ = "mined_stories"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)  # story-{uuid}
    client_id = Column(String, ForeignKey("clients.id"), nullable=False, index=True)  # Story owner
    project_id = Column(
        String, ForeignKey("projects.id"), nullable=True, index=True
    )  # Optional project link
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )  # TR-021: Story owner

    # Story classification
    story_type = Column(
        String, nullable=True
    )  # success, challenge, milestone, customer_win, lesson_learned
    title = Column(String(200), nullable=True)  # Brief story title
    summary = Column(Text, nullable=True)  # 2-3 sentence summary

    # Story content
    full_story = Column(
        JSON, nullable=True
    )  # Structured story data with context/challenge/resolution
    key_metrics = Column(
        JSON, nullable=True
    )  # Numbers, results achieved (e.g., {"revenue": "+40%", "time": "6 months"})
    emotional_hook = Column(Text, nullable=True)  # Compelling element that makes story memorable

    # Metadata
    source = Column(
        String(100), nullable=True
    )  # interview, website, case_study, user_input, story_mining_tool
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("backend.models.client.Client", foreign_keys=[client_id])
    project = relationship("backend.models.project.Project", foreign_keys=[project_id])
    user = relationship("backend.models.user.User", foreign_keys=[user_id])  # TR-021: Story owner
    usage_records = relationship("StoryUsage", back_populates="story", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MinedStory {self.title or self.id}>"


class StoryUsage(Base):
    """
    Tracks when/where a mined story has been used.

    Enables:
    - Preventing story reuse on same platform
    - Analytics on story effectiveness
    - Understanding which stories work best
    """

    __tablename__ = "story_usage"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)  # usage-{uuid}
    story_id = Column(String, ForeignKey("mined_stories.id"), nullable=False, index=True)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False, index=True)
    template_id = Column(Integer, nullable=True)  # Template number (1-15)

    # Platform tracking (prevents reuse on same platform)
    platform = Column(
        String(50), nullable=True, index=True
    )  # linkedin, twitter, facebook, blog, email

    # Usage classification
    usage_type = Column(
        String(50), nullable=True
    )  # primary (main story), supporting (example), reference (brief mention)

    # Metadata
    used_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    story = relationship("MinedStory", back_populates="usage_records")
    post = relationship("backend.models.post.Post", foreign_keys=[post_id])

    def __repr__(self):
        return f"<StoryUsage {self.story_id} on {self.platform}>"
