"""
Story service for managing mined client stories.

Provides CRUD operations and story usage tracking.
"""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import MinedStory, StoryUsage
from backend.schemas import (
    StoryCreate,
    StoryUpdate,
    StoryUsageCreate,
    StoryAnalytics,
)
from backend.utils.logger import logger


class StoryService:
    """Service for managing mined stories and usage tracking"""

    # ==================== Story CRUD ====================

    def create_story(self, db: Session, story: StoryCreate, user_id: str) -> MinedStory:
        """
        Create a new mined story.

        Args:
            db: Database session
            story: Story data
            user_id: ID of user creating the story (TR-021: ownership)

        Returns:
            Created MinedStory instance
        """
        story_id = f"story-{uuid.uuid4().hex[:12]}"
        logger.info(f"Creating story: {story_id} for client {story.client_id}")

        story_data = story.model_dump()
        story_data["user_id"] = user_id  # TR-021: Set owner
        db_story = MinedStory(id=story_id, **story_data)

        db.add(db_story)
        db.commit()
        db.refresh(db_story)

        logger.info(f"Story created: {story_id}")
        return db_story

    def get_story(self, db: Session, story_id: str) -> Optional[MinedStory]:
        """Get a story by ID"""
        return db.query(MinedStory).filter(MinedStory.id == story_id).first()

    def get_client_stories(
        self,
        db: Session,
        client_id: str,
        story_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MinedStory]:
        """
        Get all stories for a client.

        Args:
            db: Database session
            client_id: Client ID
            story_type: Optional filter by story type
            limit: Max stories to return

        Returns:
            List of MinedStory instances
        """
        query = db.query(MinedStory).filter(MinedStory.client_id == client_id)

        if story_type:
            query = query.filter(MinedStory.story_type == story_type)

        return query.order_by(MinedStory.created_at.desc()).limit(limit).all()

    def update_story(
        self, db: Session, story_id: str, story_update: StoryUpdate
    ) -> Optional[MinedStory]:
        """
        Update a story.

        Args:
            db: Database session
            story_id: Story ID
            story_update: Fields to update

        Returns:
            Updated MinedStory instance or None if not found
        """
        db_story = self.get_story(db, story_id)
        if not db_story:
            return None

        update_data = story_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_story, key, value)

        db.commit()
        db.refresh(db_story)

        logger.info(f"Story updated: {story_id}")
        return db_story

    def delete_story(self, db: Session, story_id: str) -> bool:
        """
        Delete a story.

        Args:
            db: Database session
            story_id: Story ID

        Returns:
            True if deleted, False if not found
        """
        db_story = self.get_story(db, story_id)
        if not db_story:
            return False

        db.delete(db_story)
        db.commit()

        logger.info(f"Story deleted: {story_id}")
        return True

    # ==================== Story Usage Tracking ====================

    def track_story_usage(self, db: Session, usage: StoryUsageCreate) -> StoryUsage:
        """
        Track that a story was used in a post.

        Args:
            db: Database session
            usage: Story usage data

        Returns:
            Created StoryUsage instance
        """
        usage_id = f"usage-{uuid.uuid4().hex[:12]}"
        logger.info(
            f"Tracking story usage: {usage.story_id} in post {usage.post_id} on {usage.platform}"
        )

        usage_data = usage.model_dump()
        db_usage = StoryUsage(id=usage_id, **usage_data)

        db.add(db_usage)
        db.commit()
        db.refresh(db_usage)

        logger.info(f"Story usage tracked: {usage_id}")
        return db_usage

    def get_story_usage(self, db: Session, story_id: str) -> List[StoryUsage]:
        """Get all usage records for a story"""
        return (
            db.query(StoryUsage)
            .filter(StoryUsage.story_id == story_id)
            .order_by(StoryUsage.used_at.desc())
            .all()
        )

    def is_story_used_on_platform(self, db: Session, story_id: str, platform: str) -> bool:
        """
        Check if a story has already been used on a specific platform.

        Args:
            db: Database session
            story_id: Story ID
            platform: Platform name

        Returns:
            True if story has been used on this platform
        """
        usage = (
            db.query(StoryUsage)
            .filter(
                StoryUsage.story_id == story_id,
                StoryUsage.platform == platform,
            )
            .first()
        )
        return usage is not None

    def get_available_stories(
        self,
        db: Session,
        client_id: str,
        platform: Optional[str] = None,
        story_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MinedStory]:
        """
        Get stories that haven't been used on the specified platform.

        Args:
            db: Database session
            client_id: Client ID
            platform: Platform to exclude used stories from
            story_type: Optional filter by story type
            limit: Max stories to return

        Returns:
            List of available MinedStory instances
        """
        query = db.query(MinedStory).filter(MinedStory.client_id == client_id)

        if story_type:
            query = query.filter(MinedStory.story_type == story_type)

        # Exclude stories already used on this platform
        if platform:
            used_story_ids = (
                db.query(StoryUsage.story_id).filter(StoryUsage.platform == platform).distinct()
            )
            query = query.filter(~MinedStory.id.in_(used_story_ids))

        return query.order_by(MinedStory.created_at.desc()).limit(limit).all()

    # ==================== Analytics ====================

    def get_story_analytics(self, db: Session, story_id: str) -> Optional[StoryAnalytics]:
        """
        Get analytics for a story.

        Args:
            db: Database session
            story_id: Story ID

        Returns:
            StoryAnalytics or None if story not found
        """
        story = self.get_story(db, story_id)
        if not story:
            return None

        usage_records = self.get_story_usage(db, story_id)

        platforms_used = list(set([u.platform for u in usage_records if u.platform]))
        templates_used = list(set([u.template_id for u in usage_records if u.template_id]))

        first_used = min([u.used_at for u in usage_records]) if usage_records else None
        last_used = max([u.used_at for u in usage_records]) if usage_records else None

        return StoryAnalytics(
            story_id=story_id,
            title=story.title,
            total_uses=len(usage_records),
            platforms_used=platforms_used,
            templates_used=templates_used,
            first_used=first_used,
            last_used=last_used,
        )

    def get_client_story_analytics(self, db: Session, client_id: str) -> List[StoryAnalytics]:
        """
        Get analytics for all stories for a client.

        Args:
            db: Database session
            client_id: Client ID

        Returns:
            List of StoryAnalytics
        """
        stories = self.get_client_stories(db, client_id)
        analytics = []

        for story in stories:
            story_analytics = self.get_story_analytics(db, story.id)
            if story_analytics:
                analytics.append(story_analytics)

        return analytics


# Global instance
story_service = StoryService()
