"""
Cache Management Router

Provides endpoints to monitor and manage the application cache.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.models import User
from backend.utils.auth import get_current_active_superuser
from backend.utils.cache import get_cache


router = APIRouter(prefix="/cache", tags=["cache"])


class CacheStats(BaseModel):
    """Cache statistics"""

    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Get cache statistics (admin only).

    Returns metrics about cache usage and performance.
    """
    cache = get_cache()
    stats = cache.get_stats()
    return CacheStats(**stats)


@router.post("/clear")
async def clear_cache(
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Clear all cache entries (admin only).

    Use sparingly - clears all cached data.
    """
    cache = get_cache()
    await cache.clear()
    return {"message": "Cache cleared successfully"}


@router.delete("/pattern/{pattern:path}")
async def invalidate_cache_pattern(
    pattern: str,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Invalidate cache entries matching a pattern (admin only).

    Args:
        pattern: Pattern to match (supports * wildcard)

    Example:
        DELETE /api/cache/pattern/research_results:*
    """
    cache = get_cache()
    await cache.invalidate_pattern(pattern)
    return {"message": f"Invalidated cache entries matching: {pattern}"}
