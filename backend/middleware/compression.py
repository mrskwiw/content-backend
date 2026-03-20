"""
Compression Middleware

Enables gzip compression for API responses to reduce bandwidth usage.
Especially beneficial for large payloads like batch generation responses.
"""

from fastapi.middleware.gzip import GZipMiddleware


def add_compression_middleware(app):
    """
    Add GZip compression middleware to the FastAPI application.

    Args:
        app: FastAPI application instance

    Configuration:
        - minimum_size: 500 bytes (don't compress tiny responses)
        - Automatically compresses responses with Accept-Encoding: gzip
        - Adds Content-Encoding: gzip header to compressed responses

    Expected impact:
        - 70-85% reduction for JSON responses
        - 60-75% reduction for large text payloads
        - Minimal CPU overhead (gzip level 6)
    """
    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,  # Only compress responses > 500 bytes
    )
