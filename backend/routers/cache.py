"""
Cache Management Router

Provides endpoints to monitor and manage the application cache.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.models import User
from backend.middleware.auth_dependency import get_current_user
from backend.utils.cache import get_cache


router = APIRouter(prefix="/cache", tags=["cache"])


class CacheStats(BaseModel):
    """Cache statistics"""

    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is an admin (superuser)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
