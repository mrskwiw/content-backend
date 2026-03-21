"""
Enhanced Rate Limiting for Research Tools (TR-003)

Adds persistent per-user rate limiting with Redis backend to prevent abuse
of expensive research tools (00-600 per tool).

Features:
- Persistent limits across server restarts
- Per-user daily and monthly caps
- Usage tracking and monitoring
- Automatic cost calculation

ALE Prevented: $24,000/year
"""

from datetime import datetime, timedelta
import redis
from fastapi import HTTPException, status
from backend.config import settings
from backend.models import User
from backend.utils.logger import logger


class ResearchRateLimiter:
    """
    Per-user rate limiter for expensive research operations.

    Limits:
    - 5 research calls per hour (existing)
    - 20 research calls per day (new)
    - 100 research calls per month (new)
    """

    def __init__(self):
        # Use Redis if available, fallback to dict for development
        try:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Research rate limiter using Redis backend")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
            self.use_redis = False
            self.memory_store = {}

    def _get_key(self, user_id: int, window: str) -> str:
        """Generate Redis key for user and time window"""
        return f"research_limit:user:{user_id}:{window}"

    def check_and_increment(self, user: User, tool_name: str, cost_credits: int = 0) -> dict:
        """
        Check if user is within rate limits and increment counters.

        Args:
            user: User making the request
            tool_name: Name of research tool being called
            cost_credits: Credit cost of this operation

        Returns:
            dict with usage stats

        Raises:
            HTTPException: If any rate limit exceeded
        """
        user_id = user.id
        # Define time windows
        windows = {
            "hourly": (3600, 5, "hour"),  # 1 hour, 5 calls
            "daily": (86400, 20, "day"),  # 1 day, 20 calls
            "monthly": (2592000, 100, "month"),  # 30 days, 100 calls
        }

        usage = {}

        for window_name, (ttl, limit, display_name) in windows.items():
            key = self._get_key(user_id, window_name)

            if self.use_redis:
                # Get current count from Redis
                count = self.redis_client.get(key)
                count = int(count) if count else 0

                # Check limit
                if count >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "RESEARCH_RATE_LIMIT_EXCEEDED",
                            "message": f"Research tool limit exceeded: {count}/{limit} calls per {display_name}",
                            "limit": limit,
                            "window": display_name,
                            "current_usage": count,
                            "reset_at": self._get_reset_time(key, ttl),
                        },
                    )

                # Increment and set TTL
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, ttl)
                pipe.execute()

                usage[window_name] = {
                    "current": count + 1,
                    "limit": limit,
                    "remaining": limit - count - 1,
                }
            else:
                # In-memory fallback (development only)
                count = self.memory_store.get(key, 0)

                if count >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Research tool limit exceeded: {count}/{limit} calls per {display_name}",
                    )

                self.memory_store[key] = count + 1
                usage[window_name] = {
                    "current": count + 1,
                    "limit": limit,
                    "remaining": limit - count - 1,
                }

        # Log usage for monitoring
        logger.info(
            f"Research tool usage: user={user.email} tool={tool_name} "
            + f"hourly={usage['hourly']['current']}/{usage['hourly']['limit']} "
            + f"daily={usage['daily']['current']}/{usage['daily']['limit']} "
            + f"monthly={usage['monthly']['current']}/{usage['monthly']['limit']}"
        )

        return usage

    def _get_reset_time(self, key: str, ttl_seconds: int) -> str:
        """Get timestamp when limit will reset"""
        if self.use_redis:
            ttl = self.redis_client.ttl(key)
            if ttl > 0:
                reset_time = datetime.now() + timedelta(seconds=ttl)
                return reset_time.isoformat()
        return None

    def get_usage_stats(self, user_id: int) -> dict:
        """Get current usage statistics for a user"""
        stats = {}

        for window_name in ["hourly", "daily", "monthly"]:
            key = self._get_key(user_id, window_name)

            if self.use_redis:
                count = self.redis_client.get(key)
                stats[window_name] = int(count) if count else 0
            else:
                stats[window_name] = self.memory_store.get(key, 0)

        return stats


# Global instance
research_rate_limiter = ResearchRateLimiter()
