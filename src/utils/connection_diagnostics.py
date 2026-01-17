"""Connection diagnostics module for detailed error analysis and reporting.

Provides comprehensive diagnostics for API connection issues including:
- DNS resolution checks
- Network connectivity tests
- SSL/TLS verification
- Timeout analysis
- Error classification and reporting
"""

import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .logger import logger


class ConnectionErrorType(Enum):
    """Classification of connection error types."""

    DNS_RESOLUTION_FAILED = "dns_resolution_failed"
    CONNECTION_REFUSED = "connection_refused"
    CONNECTION_TIMEOUT = "connection_timeout"
    SSL_CERTIFICATE_ERROR = "ssl_certificate_error"
    SSL_HANDSHAKE_FAILED = "ssl_handshake_failed"
    NETWORK_UNREACHABLE = "network_unreachable"
    HOST_UNREACHABLE = "host_unreachable"
    CONNECTION_RESET = "connection_reset"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION_FAILED = "authentication_failed"
    SERVER_ERROR = "server_error"
    PROXY_ERROR = "proxy_error"
    UNKNOWN = "unknown"


@dataclass
class ConnectionDiagnostics:
    """Detailed diagnostics for a connection attempt."""

    timestamp: datetime = field(default_factory=datetime.now)
    endpoint: str = ""
    error_type: ConnectionErrorType = ConnectionErrorType.UNKNOWN
    error_message: str = ""
    error_code: Optional[int] = None

    # Timing information
    dns_resolution_time_ms: Optional[float] = None
    connection_time_ms: Optional[float] = None
    ssl_handshake_time_ms: Optional[float] = None
    total_time_ms: Optional[float] = None

    # Network diagnostics
    dns_resolved: bool = False
    resolved_ip: Optional[str] = None
    port_open: bool = False
    ssl_valid: bool = False
    ssl_expiry: Optional[datetime] = None

    # Request context
    attempt_number: int = 1
    max_attempts: int = 3
    retry_delay_seconds: float = 0

    # Additional context
    raw_exception: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnostics to dictionary for logging/reporting."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "timing": {
                "dns_resolution_ms": self.dns_resolution_time_ms,
                "connection_ms": self.connection_time_ms,
                "ssl_handshake_ms": self.ssl_handshake_time_ms,
                "total_ms": self.total_time_ms,
            },
            "network": {
                "dns_resolved": self.dns_resolved,
                "resolved_ip": self.resolved_ip,
                "port_open": self.port_open,
                "ssl_valid": self.ssl_valid,
                "ssl_expiry": self.ssl_expiry.isoformat() if self.ssl_expiry else None,
            },
            "retry": {
                "attempt": self.attempt_number,
                "max_attempts": self.max_attempts,
                "delay_seconds": self.retry_delay_seconds,
            },
            "raw_exception": self.raw_exception,
            "suggestions": self.suggestions,
        }

    def to_report(self) -> str:
        """Generate human-readable diagnostic report."""
        lines = [
            "=" * 60,
            "CONNECTION DIAGNOSTIC REPORT",
            "=" * 60,
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Endpoint: {self.endpoint}",
            f"Error Type: {self.error_type.value.upper().replace('_', ' ')}",
            f"Error Message: {self.error_message}",
            "",
            "--- NETWORK STATUS ---",
            f"DNS Resolution: {'✓ Success' if self.dns_resolved else '✗ Failed'}",
        ]

        if self.resolved_ip:
            lines.append(f"Resolved IP: {self.resolved_ip}")

        lines.extend(
            [
                f"Port Accessible: {'✓ Yes' if self.port_open else '✗ No'}",
                f"SSL/TLS Valid: {'✓ Yes' if self.ssl_valid else '✗ No'}",
            ]
        )

        if self.ssl_expiry:
            lines.append(f"SSL Expiry: {self.ssl_expiry.strftime('%Y-%m-%d')}")

        lines.extend(
            [
                "",
                "--- TIMING ---",
            ]
        )

        if self.dns_resolution_time_ms is not None:
            lines.append(f"DNS Resolution: {self.dns_resolution_time_ms:.1f}ms")
        if self.connection_time_ms is not None:
            lines.append(f"Connection: {self.connection_time_ms:.1f}ms")
        if self.ssl_handshake_time_ms is not None:
            lines.append(f"SSL Handshake: {self.ssl_handshake_time_ms:.1f}ms")
        if self.total_time_ms is not None:
            lines.append(f"Total: {self.total_time_ms:.1f}ms")

        lines.extend(
            [
                "",
                "--- RETRY STATUS ---",
                f"Attempt: {self.attempt_number} of {self.max_attempts}",
                f"Retry Delay: {self.retry_delay_seconds:.1f}s",
            ]
        )

        if self.suggestions:
            lines.extend(
                [
                    "",
                    "--- SUGGESTIONS ---",
                ]
            )
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"{i}. {suggestion}")

        if self.raw_exception:
            lines.extend(
                [
                    "",
                    "--- RAW EXCEPTION ---",
                    self.raw_exception[:500],  # Truncate long exceptions
                ]
            )

        lines.append("=" * 60)
        return "\n".join(lines)


class ConnectionDiagnosticsRunner:
    """Runs connection diagnostics and classifies errors."""

    ANTHROPIC_API_HOST = "api.anthropic.com"
    ANTHROPIC_API_PORT = 443

    def __init__(self, timeout: float = 10.0):
        """Initialize diagnostics runner.

        Args:
            timeout: Timeout for diagnostic checks in seconds.
        """
        self.timeout = timeout

    def check_dns_resolution(self, hostname: str) -> tuple[bool, Optional[str], Optional[float]]:
        """Check DNS resolution for a hostname.

        Args:
            hostname: Hostname to resolve.

        Returns:
            Tuple of (success, resolved_ip, time_ms).
        """
        start = time.perf_counter()
        try:
            ip = socket.gethostbyname(hostname)
            elapsed = (time.perf_counter() - start) * 1000
            return True, ip, elapsed
        except socket.gaierror as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"DNS resolution failed for {hostname}: {e}")
            return False, None, elapsed

    def check_port_connectivity(self, hostname: str, port: int) -> tuple[bool, Optional[float]]:
        """Check if a port is accessible.

        Args:
            hostname: Hostname to connect to.
            port: Port number to check.

        Returns:
            Tuple of (success, time_ms).
        """
        start = time.perf_counter()
        try:
            sock = socket.create_connection((hostname, port), timeout=self.timeout)
            elapsed = (time.perf_counter() - start) * 1000
            sock.close()
            return True, elapsed
        except (socket.timeout, socket.error) as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"Port connectivity check failed for {hostname}:{port}: {e}")
            return False, elapsed

    def check_ssl_certificate(
        self, hostname: str, port: int = 443
    ) -> tuple[bool, Optional[datetime], Optional[float]]:
        """Check SSL certificate validity.

        Args:
            hostname: Hostname to check.
            port: Port number (default 443).

        Returns:
            Tuple of (valid, expiry_date, handshake_time_ms).
        """
        start = time.perf_counter()
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    elapsed = (time.perf_counter() - start) * 1000
                    cert = ssock.getpeercert()
                    if cert:
                        # Parse expiry date
                        not_after = cert.get("notAfter")
                        if not_after and isinstance(not_after, str):
                            # Format: 'Sep 15 00:00:00 2025 GMT'
                            try:
                                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                                return True, expiry, elapsed
                            except ValueError:
                                return True, None, elapsed
                    return True, None, elapsed
        except ssl.SSLError as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"SSL check failed for {hostname}: {e}")
            return False, None, elapsed
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"SSL check error for {hostname}: {e}")
            return False, None, elapsed

    def classify_error(self, exception: Exception) -> ConnectionErrorType:
        """Classify an exception into a connection error type.

        Args:
            exception: The exception to classify.

        Returns:
            ConnectionErrorType classification.
        """
        error_str = str(exception).lower()
        exception_type = type(exception).__name__

        # DNS errors
        if isinstance(exception, socket.gaierror) or "getaddrinfo" in error_str:
            return ConnectionErrorType.DNS_RESOLUTION_FAILED

        # Connection errors
        if "connection refused" in error_str or "errno 111" in error_str:
            return ConnectionErrorType.CONNECTION_REFUSED

        if "timed out" in error_str or "timeout" in error_str:
            return ConnectionErrorType.CONNECTION_TIMEOUT

        if "connection reset" in error_str or "errno 104" in error_str:
            return ConnectionErrorType.CONNECTION_RESET

        # SSL errors
        if "ssl" in error_str or "certificate" in error_str:
            if "certificate" in error_str and ("verify" in error_str or "invalid" in error_str):
                return ConnectionErrorType.SSL_CERTIFICATE_ERROR
            return ConnectionErrorType.SSL_HANDSHAKE_FAILED

        # Network unreachable
        if "network is unreachable" in error_str or "errno 101" in error_str:
            return ConnectionErrorType.NETWORK_UNREACHABLE

        if "host unreachable" in error_str or "errno 113" in error_str:
            return ConnectionErrorType.HOST_UNREACHABLE

        # Rate limiting (check exception type name from anthropic)
        if "ratelimit" in exception_type.lower() or "rate" in error_str and "limit" in error_str:
            return ConnectionErrorType.RATE_LIMITED

        # Authentication
        if "401" in error_str or "authentication" in error_str or "unauthorized" in error_str:
            return ConnectionErrorType.AUTHENTICATION_FAILED

        # Server errors
        if any(code in error_str for code in ["500", "502", "503", "504"]):
            return ConnectionErrorType.SERVER_ERROR

        # Proxy errors
        if "proxy" in error_str:
            return ConnectionErrorType.PROXY_ERROR

        return ConnectionErrorType.UNKNOWN

    def get_suggestions(self, error_type: ConnectionErrorType) -> List[str]:
        """Get troubleshooting suggestions for an error type.

        Args:
            error_type: The classified error type.

        Returns:
            List of troubleshooting suggestions.
        """
        suggestions_map = {
            ConnectionErrorType.DNS_RESOLUTION_FAILED: [
                "Check your internet connection",
                "Verify DNS settings (try 8.8.8.8 or 1.1.1.1)",
                "Check if api.anthropic.com is accessible from your network",
                "Try flushing DNS cache: ipconfig /flushdns (Windows) or sudo dscacheutil -flushcache (macOS)",
            ],
            ConnectionErrorType.CONNECTION_REFUSED: [
                "The Anthropic API server may be temporarily unavailable",
                "Check if a firewall is blocking outbound connections on port 443",
                "Verify your network allows HTTPS connections",
            ],
            ConnectionErrorType.CONNECTION_TIMEOUT: [
                "Your network connection may be slow or unstable",
                "Check for network congestion or bandwidth issues",
                "Try increasing the timeout value in settings",
                "Consider using a more stable network connection",
            ],
            ConnectionErrorType.SSL_CERTIFICATE_ERROR: [
                "Your system's SSL certificates may be outdated",
                "Check system time/date settings (must be accurate for SSL)",
                "Verify no proxy is intercepting HTTPS traffic",
                "Update your SSL certificate store",
            ],
            ConnectionErrorType.SSL_HANDSHAKE_FAILED: [
                "SSL/TLS handshake failed - possible protocol mismatch",
                "Ensure your Python installation supports TLS 1.2+",
                "Check for corporate firewall/proxy SSL inspection",
            ],
            ConnectionErrorType.NETWORK_UNREACHABLE: [
                "No route to the Anthropic API servers",
                "Check your internet connection",
                "Verify network adapter is enabled and connected",
                "Check routing table if using VPN or custom networking",
            ],
            ConnectionErrorType.HOST_UNREACHABLE: [
                "Cannot reach api.anthropic.com",
                "Check if the host is blocked by your network",
                "Verify firewall rules allow outbound traffic",
            ],
            ConnectionErrorType.CONNECTION_RESET: [
                "Connection was reset by the remote server",
                "May be a transient network issue - retry should help",
                "Check for network instability",
            ],
            ConnectionErrorType.RATE_LIMITED: [
                "You've exceeded the API rate limit",
                "Wait before making more requests",
                "Consider implementing request throttling",
                "Check your API plan limits at console.anthropic.com",
            ],
            ConnectionErrorType.AUTHENTICATION_FAILED: [
                "Your API key may be invalid or expired",
                "Verify ANTHROPIC_API_KEY is set correctly",
                "Check API key at console.anthropic.com",
                "Ensure no extra whitespace in API key",
            ],
            ConnectionErrorType.SERVER_ERROR: [
                "Anthropic API is experiencing issues",
                "Check status.anthropic.com for outages",
                "Retry with exponential backoff",
            ],
            ConnectionErrorType.PROXY_ERROR: [
                "Check proxy configuration",
                "Verify proxy credentials if required",
                "Try connecting without proxy",
            ],
            ConnectionErrorType.UNKNOWN: [
                "An unexpected error occurred",
                "Check the raw exception for more details",
                "Verify internet connectivity",
                "Try restarting the application",
            ],
        }
        return suggestions_map.get(error_type, suggestions_map[ConnectionErrorType.UNKNOWN])

    def run_full_diagnostics(
        self,
        exception: Optional[Exception] = None,
        endpoint: str = "https://api.anthropic.com",
        attempt: int = 1,
        max_attempts: int = 3,
        retry_delay: float = 0,
    ) -> ConnectionDiagnostics:
        """Run comprehensive connection diagnostics.

        Args:
            exception: The exception that triggered diagnostics (if any).
            endpoint: The API endpoint being accessed.
            attempt: Current attempt number.
            max_attempts: Maximum retry attempts.
            retry_delay: Delay before next retry.

        Returns:
            ConnectionDiagnostics with full analysis.
        """
        diag = ConnectionDiagnostics(
            endpoint=endpoint,
            attempt_number=attempt,
            max_attempts=max_attempts,
            retry_delay_seconds=retry_delay,
        )

        # Parse hostname from endpoint
        parsed = urlparse(endpoint)
        hostname = parsed.hostname or self.ANTHROPIC_API_HOST
        port = parsed.port or self.ANTHROPIC_API_PORT

        total_start = time.perf_counter()

        # Run DNS check
        dns_success, resolved_ip, dns_time = self.check_dns_resolution(hostname)
        diag.dns_resolved = dns_success
        diag.resolved_ip = resolved_ip
        diag.dns_resolution_time_ms = dns_time

        # Run port connectivity check if DNS succeeded
        if dns_success:
            port_success, conn_time = self.check_port_connectivity(hostname, port)
            diag.port_open = port_success
            diag.connection_time_ms = conn_time

            # Run SSL check if port is open
            if port_success:
                ssl_valid, ssl_expiry, ssl_time = self.check_ssl_certificate(hostname, port)
                diag.ssl_valid = ssl_valid
                diag.ssl_expiry = ssl_expiry
                diag.ssl_handshake_time_ms = ssl_time

        diag.total_time_ms = (time.perf_counter() - total_start) * 1000

        # Classify error if exception provided
        if exception:
            diag.error_type = self.classify_error(exception)
            diag.error_message = str(exception)
            diag.raw_exception = f"{type(exception).__name__}: {exception}"

            # Extract error code if available
            if hasattr(exception, "status_code"):
                diag.error_code = exception.status_code
            elif hasattr(exception, "errno"):
                diag.error_code = exception.errno

        # Add suggestions based on diagnostics
        if exception:
            diag.suggestions = self.get_suggestions(diag.error_type)
        elif not dns_success:
            diag.error_type = ConnectionErrorType.DNS_RESOLUTION_FAILED
            diag.suggestions = self.get_suggestions(ConnectionErrorType.DNS_RESOLUTION_FAILED)
        elif not diag.port_open:
            diag.error_type = ConnectionErrorType.CONNECTION_REFUSED
            diag.suggestions = self.get_suggestions(ConnectionErrorType.CONNECTION_REFUSED)
        elif not diag.ssl_valid:
            diag.error_type = ConnectionErrorType.SSL_CERTIFICATE_ERROR
            diag.suggestions = self.get_suggestions(ConnectionErrorType.SSL_CERTIFICATE_ERROR)

        return diag


# Singleton diagnostics runner
_diagnostics_runner: Optional[ConnectionDiagnosticsRunner] = None


def get_diagnostics_runner() -> ConnectionDiagnosticsRunner:
    """Get or create the singleton diagnostics runner."""
    global _diagnostics_runner
    if _diagnostics_runner is None:
        _diagnostics_runner = ConnectionDiagnosticsRunner()
    return _diagnostics_runner


def diagnose_connection_error(
    exception: Exception,
    endpoint: str = "https://api.anthropic.com",
    attempt: int = 1,
    max_attempts: int = 3,
    retry_delay: float = 0,
) -> ConnectionDiagnostics:
    """Convenience function to diagnose a connection error.

    Args:
        exception: The exception that occurred.
        endpoint: The API endpoint being accessed.
        attempt: Current attempt number.
        max_attempts: Maximum retry attempts.
        retry_delay: Delay before next retry.

    Returns:
        ConnectionDiagnostics with analysis.
    """
    runner = get_diagnostics_runner()
    return runner.run_full_diagnostics(
        exception=exception,
        endpoint=endpoint,
        attempt=attempt,
        max_attempts=max_attempts,
        retry_delay=retry_delay,
    )


def check_anthropic_connectivity() -> ConnectionDiagnostics:
    """Quick health check for Anthropic API connectivity.

    Returns:
        ConnectionDiagnostics with current connectivity status.
    """
    runner = get_diagnostics_runner()
    return runner.run_full_diagnostics()
