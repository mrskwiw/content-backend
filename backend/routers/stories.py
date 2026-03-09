"""
Story API endpoints.

Handles mined client stories and usage tracking.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.auth_dependency import get_current_user
from backend.middleware.authorization import _check_ownership
from backend.models import User
from backend.schemas import (
    StoryCreate,
    StoryUpdate,
    StoryResponse,
    StoryListResponse,
    StoryUsageCreate,
    StoryUsageResponse,
    AvailableStoriesRequest,
    StoryAnalytics,
)
from backend.services import crud
from backend.services.story_service import story_service
from backend.utils.http_rate_limiter import standard_limiter

router = APIRouter()


# ==================== Story CRUD Endpoints ====================


@router.post("/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
@standard_limiter.limit("100/hour")
async def create_story(
    request: Request,
    story: StoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new mined story.

    **Authentication required.**

    Args:
        story: Story data including client_id

    Returns:
        Created story with usage stats

    Raises:
        HTTPException 403: User doesn't own the client
        HTTPException 404: Client not found
    """
    # Verify client exists and user owns it (TR-021: IDOR prevention)
    client = crud.get_client(db, story.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {story.client_id} not found",
        )

    if not _check_ownership("Client", client, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this client",
        )

    # Create story
    db_story = story_service.create_story(db, story, current_user.id)

    # Add usage stats
    story_dict = StoryResponse.model_validate(db_story).model_dump()
    story_dict["usage_count"] = 0
    story_dict["platforms_used"] = []

    return story_dict


@router.get("/{story_id}", response_model=StoryResponse)
@standard_limiter.limit("100/minute")
async def get_story(
    request: Request,
    story_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a story by ID.

    **Authentication required.**

    Returns:
        Story with usage stats

    Raises:
        HTTPException 404: Story not found
        HTTPException 403: User doesn't own the story
    """
    story = story_service.get_story(db, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    # TR-021: Verify ownership via user_id
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this story",
        )

    # Get usage stats
    usage_records = story_service.get_story_usage(db, story_id)
    platforms_used = list(set([u.platform for u in usage_records if u.platform]))

    story_dict = StoryResponse.model_validate(story).model_dump()
    story_dict["usage_count"] = len(usage_records)
    story_dict["platforms_used"] = platforms_used

    return story_dict


@router.get("/client/{client_id}", response_model=StoryListResponse)
@standard_limiter.limit("100/minute")
async def get_client_stories(
    request: Request,
    client_id: str,
    story_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all stories for a client.

    **Authentication required.**

    Args:
        client_id: Client ID
        story_type: Optional filter by story type
        limit: Max stories to return (default: 100)

    Returns:
        List of stories with usage stats

    Raises:
        HTTPException 403: User doesn't own the client
        HTTPException 404: Client not found
    """
    # Verify client exists and user owns it
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found",
        )

    if not _check_ownership("Client", client, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this client",
        )

    # Get stories
    stories = story_service.get_client_stories(db, client_id, story_type, limit)

    # Add usage stats to each story
    story_responses = []
    for story in stories:
        usage_records = story_service.get_story_usage(db, story.id)
        platforms_used = list(set([u.platform for u in usage_records if u.platform]))

        story_dict = StoryResponse.model_validate(story).model_dump()
        story_dict["usage_count"] = len(usage_records)
        story_dict["platforms_used"] = platforms_used
        story_responses.append(StoryResponse(**story_dict))

    return StoryListResponse(stories=story_responses, total=len(story_responses))


@router.put("/{story_id}", response_model=StoryResponse)
@standard_limiter.limit("100/hour")
async def update_story(
    request: Request,
    story_id: str,
    story_update: StoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a story.

    **Authentication required.**

    Raises:
        HTTPException 404: Story not found
        HTTPException 403: User doesn't own the story
    """
    # Verify story exists and user owns it
    story = story_service.get_story(db, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this story",
        )

    # Update story
    updated_story = story_service.update_story(db, story_id, story_update)

    # Add usage stats
    usage_records = story_service.get_story_usage(db, story_id)
    platforms_used = list(set([u.platform for u in usage_records if u.platform]))

    story_dict = StoryResponse.model_validate(updated_story).model_dump()
    story_dict["usage_count"] = len(usage_records)
    story_dict["platforms_used"] = platforms_used

    return story_dict


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
@standard_limiter.limit("100/hour")
async def delete_story(
    request: Request,
    story_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a story.

    **Authentication required.**

    Raises:
        HTTPException 404: Story not found
        HTTPException 403: User doesn't own the story
    """
    # Verify story exists and user owns it
    story = story_service.get_story(db, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this story",
        )

    # Delete story
    story_service.delete_story(db, story_id)


# ==================== Story Usage Endpoints ====================


@router.post("/usage", response_model=StoryUsageResponse, status_code=status.HTTP_201_CREATED)
@standard_limiter.limit("100/hour")
async def track_story_usage(
    request: Request,
    usage: StoryUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Track that a story was used in a post.

    **Authentication required.**

    Args:
        usage: Story usage data

    Raises:
        HTTPException 404: Story or post not found
        HTTPException 403: User doesn't own the story
    """
    # Verify story exists and user owns it
    story = story_service.get_story(db, usage.story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {usage.story_id} not found",
        )

    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this story",
        )

    # Track usage
    db_usage = story_service.track_story_usage(db, usage)

    return StoryUsageResponse.model_validate(db_usage)


@router.post("/available", response_model=StoryListResponse)
@standard_limiter.limit("100/minute")
async def get_available_stories(
    request: Request,
    req: AvailableStoriesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get stories that haven't been used on the specified platform.

    **Authentication required.**

    Useful for content generation to avoid story reuse on same platform.

    Args:
        req: Request with client_id, platform, story_type, limit

    Returns:
        List of available stories

    Raises:
        HTTPException 403: User doesn't own the client
        HTTPException 404: Client not found
    """
    # Verify client exists and user owns it
    client = crud.get_client(db, req.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {req.client_id} not found",
        )

    if not _check_ownership("Client", client, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this client",
        )

    # Get available stories
    stories = story_service.get_available_stories(
        db, req.client_id, req.platform, req.story_type, req.limit
    )

    # Add usage stats
    story_responses = []
    for story in stories:
        usage_records = story_service.get_story_usage(db, story.id)
        platforms_used = list(set([u.platform for u in usage_records if u.platform]))

        story_dict = StoryResponse.model_validate(story).model_dump()
        story_dict["usage_count"] = len(usage_records)
        story_dict["platforms_used"] = platforms_used
        story_responses.append(StoryResponse(**story_dict))

    return StoryListResponse(stories=story_responses, total=len(story_responses))


# ==================== Analytics Endpoints ====================


@router.get("/{story_id}/analytics", response_model=StoryAnalytics)
@standard_limiter.limit("100/minute")
async def get_story_analytics(
    request: Request,
    story_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics for a story.

    **Authentication required.**

    Shows usage stats, platforms used, templates used, etc.

    Raises:
        HTTPException 404: Story not found
        HTTPException 403: User doesn't own the story
    """
    # Verify story exists and user owns it
    story = story_service.get_story(db, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this story",
        )

    # Get analytics
    analytics = story_service.get_story_analytics(db, story_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics not found for story {story_id}",
        )

    return analytics


@router.get("/client/{client_id}/analytics", response_model=List[StoryAnalytics])
@standard_limiter.limit("100/minute")
async def get_client_story_analytics(
    request: Request,
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics for all stories for a client.

    **Authentication required.**

    Useful for understanding which stories are most effective.

    Raises:
        HTTPException 403: User doesn't own the client
        HTTPException 404: Client not found
    """
    # Verify client exists and user owns it
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found",
        )

    if not _check_ownership("Client", client, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this client",
        )

    # Get analytics
    analytics = story_service.get_client_story_analytics(db, client_id)

    return analytics
