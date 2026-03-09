"""
Pydantic schemas for Story API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class StoryBase(BaseModel):
    """Base story schema"""

    story_type: Optional[str] = Field(
        None,
        description="Story type: success, challenge, milestone, customer_win, lesson_learned",
    )
    title: Optional[str] = Field(None, max_length=200, description="Brief story title")
    summary: Optional[str] = Field(None, description="2-3 sentence summary")
    full_story: Optional[Dict[str, Any]] = Field(
        None, description="Structured story data with context/challenge/resolution"
    )
    key_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Numbers, results achieved (e.g., {'revenue': '+40%'})"
    )
    emotional_hook: Optional[str] = Field(
        None, description="Compelling element that makes story memorable"
    )
    source: Optional[str] = Field(
        None,
        max_length=100,
        description="Source: interview, website, case_study, user_input, story_mining_tool",
    )


class StoryCreate(StoryBase):
    """
    Schema for creating a story.

    TR-022: Mass assignment protection
    - Only allows story content fields
    - Protected fields set by system: id, client_id, user_id, created_at
    """

    client_id: str = Field(..., description="Client ID this story belongs to")
    project_id: Optional[str] = Field(None, description="Optional project ID")

    model_config = ConfigDict(extra="forbid")  # TR-022: Reject unknown fields


class StoryUpdate(BaseModel):
    """
    Schema for updating a story (all fields optional).

    TR-022: Mass assignment protection
    - Only allows story content fields
    - Protected fields (never updatable): id, client_id, user_id, created_at
    """

    story_type: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = None
    full_story: Optional[Dict[str, Any]] = None
    key_metrics: Optional[Dict[str, Any]] = None
    emotional_hook: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(extra="forbid")  # TR-022: Reject unknown fields


class StoryResponse(StoryBase):
    """
    Schema for story response.

    Includes all fields including read-only ones.
    """

    id: str
    client_id: str
    project_id: Optional[str]
    user_id: str
    created_at: datetime
    updated_at: datetime
    usage_count: int = Field(0, description="Number of times this story has been used")
    platforms_used: List[str] = Field(
        default_factory=list, description="Platforms where story has been used"
    )

    model_config = ConfigDict(from_attributes=True)


class StoryListResponse(BaseModel):
    """Response for list of stories"""

    stories: List[StoryResponse]
    total: int


class StoryUsageBase(BaseModel):
    """Base story usage schema"""

    platform: Optional[str] = Field(
        None,
        max_length=50,
        description="Platform: linkedin, twitter, facebook, blog, email",
    )
    usage_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Usage type: primary, supporting, reference",
    )
    template_id: Optional[int] = Field(None, description="Template number (1-15)")


class StoryUsageCreate(StoryUsageBase):
    """
    Schema for creating a story usage record.

    TR-022: Mass assignment protection
    """

    story_id: str
    post_id: str

    model_config = ConfigDict(extra="forbid")


class StoryUsageResponse(StoryUsageBase):
    """Schema for story usage response"""

    id: str
    story_id: str
    post_id: str
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailableStoriesRequest(BaseModel):
    """Request for getting available stories (excluding used on platform)"""

    client_id: str
    platform: Optional[str] = Field(
        None, description="Platform to exclude already-used stories from"
    )
    story_type: Optional[str] = Field(None, description="Filter by story type")
    limit: int = Field(10, ge=1, le=100, description="Max stories to return")


class StoryAnalytics(BaseModel):
    """Analytics for story effectiveness"""

    story_id: str
    title: Optional[str]
    total_uses: int
    platforms_used: List[str]
    templates_used: List[int]
    first_used: Optional[datetime]
    last_used: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
