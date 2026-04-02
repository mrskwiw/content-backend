"""
HTTP Rate Limiting (TR-004)

Protects API endpoints from abuse and DoS attacks by limiting request rates.

Rate Limits (from TRA report):
- /api/research/*: 5 requests/hour per IP+user (expensive AI operations $400-600/call)
- /api/auth/login: 10 requests/hour per IP (prevent brute force)
- /api/auth/register: 3 requests/hour per IP (prevent spam accounts)
- /api/assistant/*: 50 requests/hour per IP+user (Claude API chat)
- /api/generator/*: 10 requests/hour per IP+user (expensive operations)
- /api/projects/*: 100 requests/hour per user (standard operations)
- /api/briefs/*: 100 requests/hour per user (standard operations)
- /api/clients/*: 100 requests/hour per user (standard operations)
- /api/deliverables/*: 100 requests/hour per user (standard operations)
- /api/posts/*: 1000 requests/hour per user (cheap read operations)
- Default: 60 requests/minute per IP

OWASP Top 10 2021: API4:2023 - Unrestricted Resource Consumption
"""

import time
from urllib.parse import urlparse
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.config import settings


def get_real_ip(request: Request) -> str:
    """
    Extract real client IP, handling proxy headers securely.

    In production (DEBUG_MODE=False): checks X-Forwarded-For and X-Real-IP headers.
    In debug mode (DEBUG_MODE=True): ignores proxy headers to prevent IP spoofing during dev.

    Security: Always take the FIRST IP in X-Forwarded-For chain (client IP, not proxy IP).

    Returns:
        Real client IP address as string
    """
    # In debug mode, ignore proxy headers (security: can't trust them locally)
    if getattr(settings, "DEBUG_MODE", False):
        return get_remote_address(request)

    # Check X-Forwarded-For (standard proxy header)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # First IP is the client, rest are proxies - strip whitespace
        return x_forwarded_for.split(",")[0].strip()

    # Check X-Real-IP (nginx proxy header)
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()

    # Fall back to direct connection IP
    return get_remote_address(request)


def get_storage_uri() -> str:
    """
    Determine storage URI for rate limiter.

    Tries Redis first (from settings.RATE_LIMIT_STORAGE), falls back to in-memory if unavailable.

    Returns:
        Storage URI string (redis:// or memory://)
    """
    storage = getattr(settings, "RATE_LIMIT_STORAGE", "memory://")

    if not storage or storage == "memory://":
        return "memory://"

    # Try to connect to Redis to verify it's available
    try:
        import redis

        parsed = urlparse(storage)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        db_path = parsed.path.lstrip("/")
        db = int(db_path) if db_path.isdigit() else 0
        r = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=1)
        r.ping()
        r.close()
        return storage
    except Exception:
        return "memory://"


# Determine storage URI at module load time
_storage_uri = get_storage_uri()


def get_user_id_or_ip(request: Request) -> str:
    """
    Get rate limit key - user ID if authenticated, otherwise IP address.

    This allows per-user rate limiting for authenticated endpoints
    and per-IP limiting for public endpoints.
    """
    # Check if user is authenticated (from auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to real IP address (proxy-aware)
    return get_real_ip(request)


def get_composite_key(request: Request) -> str:
    """
    Combine IP + user ID to prevent VPN bypass.

    This is more secure than IP-only or user-only limiting because:
    - Prevents single user from bypassing limits via VPN/proxies
    - Prevents single IP from creating multiple accounts to bypass limits
    - Provides defense-in-depth for critical operations
    """
    ip = get_real_ip(request)
    user = getattr(request.state, "user", None)

    if user and hasattr(user, "id"):
        return f"{ip}:user-{user.id}"

    return f"{ip}:anonymous"


# Create limiter instance (default for all endpoints)
limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["60/minute"],  # Default limit for all endpoints
    storage_uri=_storage_uri,  # Determined at module load (Redis or memory fallback)
    strategy="fixed-window",  # Fixed time window
)


# Strict limiter for expensive operations (research, generation)
# Uses composite key (IP + user ID) to prevent VPN bypass
strict_limiter = Limiter(
    key_func=get_composite_key,
    default_limits=[],  # No default - explicitly set per endpoint
    storage_uri=_storage_uri,
    strategy="fixed-window",
)


# Standard limiter for normal operations (projects, clients, briefs)
standard_limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["100/hour"],  # Standard limit for authenticated operations
    storage_uri="memory://",
    strategy="fixed-window",
)


# Lenient limiter for cheap read operations (posts, health checks)
lenient_limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["1000/hour"],  # High limit for cheap operations
    storage_uri="memory://",
    strategy="fixed-window",
)


# Custom rate limit error message
def rate_limit_exceeded_handler(request: Request, exc):
    """Custom handler for rate limit exceeded errors"""
    # Parse retry_after from exc.detail (e.g. "10 per 1 hour")
    retry_after = 3600  # default 1 hour in seconds
    try:
        # slowapi puts the limit string in exc.detail
        detail = str(exc.detail) if exc.detail else ""
        if "minute" in detail:
            retry_after = 60
        elif "hour" in detail:
            retry_after = 3600
        elif "second" in detail:
            retry_after = 1
    except Exception:
        pass

    reset_at = int(time.time()) + retry_after

    headers = {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": "10",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(reset_at),
    }

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after,
                "reset_at": reset_at,
            }
        },
        headers=headers,
    )
