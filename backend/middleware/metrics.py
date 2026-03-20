"""
Metrics Middleware

Automatically tracks request duration and status for all API endpoints.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.utils.metrics import get_metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics automatically.

    Tracks:
    - Request duration (in milliseconds)
    - HTTP status codes
    - Success/failure rates
    - Response time percentiles
    """

    async def dispatch(self, request: Request, call_next):
        # Skip metrics collection for static files and health checks
        if request.url.path.startswith("/assets") or request.url.path == "/favicon.ico":
            return await call_next(request)

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response: Response = await call_next(request)
        except Exception as exc:
            # Record error metric
            duration_ms = (time.time() - start_time) * 1000
            get_metrics().record_request(
                path=request.url.path,
                method=request.method,
                status_code=500,
                duration_ms=duration_ms,
            )
            raise exc

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Record metric
        get_metrics().record_request(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Add response time header for debugging
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
