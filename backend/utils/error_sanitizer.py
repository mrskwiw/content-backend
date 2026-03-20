"""
Error Sanitization Utility (TR-010)

Prevents internal error details from leaking to clients in production.
Provides safe, user-friendly error messages while logging full details server-side.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple

from backend.config import settings

logger = logging.getLogger(__name__)

# Patterns that indicate sensitive information in error messages
SENSITIVE_PATTERNS = [
    # Database/SQL errors
    r"(psycopg2|sqlite3|sqlalchemy|postgresql|mysql)",
    r"(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\s+",
    r"(syntax error|relation|table|column|constraint)",
    # File paths
    r"(/home/|/var/|/usr/|/app/|C:\|D:\)",
    r"(\.py|\.pyc|\.pyo):\d+",
    # Stack traces
    r"(Traceback|File \"|line \d+)",
    r"(raise|exception|error).*at 0x[0-9a-f]+",
    # Credentials/secrets
    r"(password|secret|key|token|api_key|auth).*=",
    r"(sk-ant-|sk-|Bearer\s+)",
    # Internal module names
    r"(backend\.|src\.|agent\.|validators\.)",
    # IP addresses and ports
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+",
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

# Safe error messages for common error types
SAFE_ERROR_MESSAGES = {
    "database": "A database error occurred. Please try again later.",
    "validation": "The request data was invalid. Please check your input.",
    "authentication": "Authentication failed. Please check your credentials.",
    "authorization": "You don't have permission to perform this action.",
    "not_found": "The requested resource was not found.",
    "rate_limit": "Too many requests. Please try again later.",
    "timeout": "The request timed out. Please try again.",
    "external_service": "An external service is unavailable. Please try again later.",
    "file_operation": "A file operation failed. Please try again.",
    "internal": "An unexpected error occurred. Please try again later.",
}


def contains_sensitive_info(message: str) -> bool:
    """
    Check if an error message contains sensitive information.

    Args:
        message: Error message to check

    Returns:
        True if sensitive information is detected
    """
    if not message:
        return False

    for pattern in COMPILED_PATTERNS:
        if pattern.search(message):
            return True

    return False


def categorize_error(exc: Exception) -> str:
    """
    Categorize an exception to determine the appropriate safe message.

    Args:
        exc: The exception to categorize

    Returns:
        Error category key
    """
    exc_type = type(exc).__name__.lower()
    exc_message = str(exc).lower()

    # Database errors
    if any(
        db_term in exc_type or db_term in exc_message
        for db_term in ["sql", "database", "psycopg", "sqlite", "integrity", "constraint"]
    ):
        return "database"

    # Validation errors
    if any(
        val_term in exc_type or val_term in exc_message
        for val_term in ["validation", "pydantic", "schema", "invalid", "required"]
    ):
        return "validation"

    # Authentication errors
    if any(
        auth_term in exc_type or auth_term in exc_message
        for auth_term in ["auth", "credential", "token", "jwt", "login"]
    ):
        return "authentication"

    # Authorization errors
    if any(
        authz_term in exc_type or authz_term in exc_message
        for authz_term in ["permission", "forbidden", "access denied", "unauthorized"]
    ):
        return "authorization"

    # Not found errors
    if any(
        nf_term in exc_type or nf_term in exc_message
        for nf_term in ["notfound", "not found", "does not exist", "missing"]
    ):
        return "not_found"

    # Timeout errors
    if any(
        to_term in exc_type or to_term in exc_message
        for to_term in ["timeout", "timed out", "deadline"]
    ):
        return "timeout"

    # File errors
    if any(
        file_term in exc_type or file_term in exc_message
        for file_term in ["file", "path", "directory", "io", "permission"]
    ):
        return "file_operation"

    # External service errors
    if any(
        ext_term in exc_type or ext_term in exc_message
        for ext_term in ["connection", "network", "http", "api", "service", "upstream"]
    ):
        return "external_service"

    return "internal"


def sanitize_error_message(
    exc: Exception,
    include_error_code: bool = True,
) -> Tuple[str, Optional[str]]:
    """
    Sanitize an exception for client-facing response.

    Args:
        exc: The exception to sanitize
        include_error_code: Whether to include an error code

    Returns:
        Tuple of (safe_message, error_code)
    """
    # In debug mode, return the original message
    if settings.DEBUG_MODE:
        return str(exc), type(exc).__name__

    # Log the full error server-side
    logger.error(f"Error sanitized for client: {type(exc).__name__}: {exc}", exc_info=True)

    # Categorize and get safe message
    category = categorize_error(exc)
    safe_message = SAFE_ERROR_MESSAGES.get(category, SAFE_ERROR_MESSAGES["internal"])

    # Generate error code
    error_code = f"{category.upper()}_ERROR" if include_error_code else None

    return safe_message, error_code


def create_safe_error_response(
    exc: Exception,
    status_code: int = 500,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a sanitized error response dictionary.

    Args:
        exc: The exception to handle
        status_code: HTTP status code for the response
        request_id: Optional request ID for tracing

    Returns:
        Dictionary suitable for JSONResponse
    """
    safe_message, error_code = sanitize_error_message(exc)

    response = {
        "success": False,
        "error": {
            "message": safe_message,
        },
    }

    if error_code:
        response["error"]["code"] = error_code

    # Add request ID for tracing (if available)
    if request_id:
        response["error"]["request_id"] = request_id

    # In debug mode, include additional info
    if settings.DEBUG_MODE:
        response["error"]["type"] = type(exc).__name__
        response["error"]["debug_message"] = str(exc)

    return response


def sanitize_string(text: str, replacement: str = "[REDACTED]") -> str:
    """
    Remove sensitive information from a string.

    Args:
        text: Text to sanitize
        replacement: Replacement text for sensitive data

    Returns:
        Sanitized string
    """
    if not text:
        return text

    result = text
    for pattern in COMPILED_PATTERNS:
        result = pattern.sub(replacement, result)

    return result
