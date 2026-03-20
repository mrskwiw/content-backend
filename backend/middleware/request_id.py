"""
Request ID Middleware

Adds a unique request ID to each request for tracing errors across the system.
Request IDs are included in logs and error responses for debugging.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to each HTTP request.

    The request ID is:
    - Generated as a UUID4
    - Added to request.state.request_id for access in route handlers
    - Included in the X-Request-ID response header
    - Logged with each request for tracing
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Process the request
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Log error with request ID
            logger.error(
                f"Request {request_id} failed: {type(exc).__name__}: {exc}",
                exc_info=True,
                extra={"request_id": request_id},
            )
            raise

        # Add request ID to response headers for client-side tracing
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the current request.

    Args:
        request: The current FastAPI request

    Returns:
        The request ID string, or "unknown" if not available
    """
    return getattr(request.state, "request_id", "unknown")
