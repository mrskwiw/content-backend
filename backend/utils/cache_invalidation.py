"""
Cache Invalidation Helpers

Provides utilities to invalidate cached data when database entities are modified.
"""

from typing import Optional
import logging
from backend.utils.cache import get_cache

logger = logging.getLogger(__name__)


async def invalidate_project_cache(project_id: str):
    """
    Invalidate all cache entries related to a project.

    Called when project data is modified.
    """
    cache = get_cache()
    patterns = [
        f"*project:{project_id}*",
        f"*project_id={project_id}*",
        f"research_results:*project_id:{project_id}*",
        f"costs:*project_id:{project_id}*",
    ]

    for pattern in patterns:
        await cache.invalidate_pattern(pattern)

    logger.info(f"Invalidated project cache: {project_id}")


async def invalidate_client_cache(client_id: str):
    """
    Invalidate all cache entries related to a client.

    Called when client data is modified.
    """
    cache = get_cache()
    patterns = [
        f"*client:{client_id}*",
        f"*client_id={client_id}*",
        f"research_results:*client_id:{client_id}*",
        f"costs:*client_id:{client_id}*",
    ]

    for pattern in patterns:
        await cache.invalidate_pattern(pattern)

    logger.info(f"Invalidated client cache: {client_id}")


async def invalidate_research_cache(
    client_id: Optional[str] = None, project_id: Optional[str] = None
):
    """
    Invalidate research-related cache entries.

    Called when new research is completed.
    """
    cache = get_cache()

    if client_id:
        await cache.invalidate_pattern(f"research_results:*client_id:{client_id}*")
        await cache.invalidate_pattern(f"research_analytics:*client_id:{client_id}*")

    if project_id:
        await cache.invalidate_pattern(f"research_results:*project_id:{project_id}*")
        await cache.invalidate_pattern(f"research_analytics:*project_id:{project_id}*")

    logger.info(f"Invalidated research cache (client={client_id}, project={project_id})")


async def invalidate_cost_cache(user_id: str):
    """
    Invalidate cost-related cache entries for a user.

    Called when new costs are recorded.
    """
    cache = get_cache()
    patterns = [
        f"costs:*user_id:{user_id}*",
        f"user_cost_summary:*user_id:{user_id}*",
    ]

    for pattern in patterns:
        await cache.invalidate_pattern(pattern)

    logger.info(f"Invalidated cost cache: user {user_id}")


async def invalidate_all_caches():
    """
    Clear all caches.

    Use sparingly - only for maintenance or major data migrations.
    """
    cache = get_cache()
    await cache.clear()
    logger.warning("All caches cleared")
