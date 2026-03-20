"""
Application Metrics Collection

Provides lightweight metrics for monitoring application performance.
Compatible with Prometheus, Grafana, and other monitoring systems.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import statistics


@dataclass
class RequestMetric:
    """Metrics for a single request"""

    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime


@dataclass
class EndpointStats:
    """Aggregated statistics for an endpoint"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    recent_durations: List[float] = field(default_factory=list)

    def add_request(self, duration_ms: float, status_code: int):
        """Add a request to statistics"""
        self.total_requests += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        if status_code < 400:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # Keep last 100 durations for percentile calculation
        self.recent_durations.append(duration_ms)
        if len(self.recent_durations) > 100:
            self.recent_durations.pop(0)

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration"""
        return self.total_duration_ms / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def p95_duration_ms(self) -> float:
        """Calculate 95th percentile duration"""
        if not self.recent_durations:
            return 0.0
        return (
            statistics.quantiles(self.recent_durations, n=20)[18]
            if len(self.recent_durations) > 1
            else self.recent_durations[0]
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        return (
            (self.successful_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0.0
        )


class MetricsCollector:
    """
    Lightweight metrics collector for application monitoring.

    Collects:
    - Request count and duration by endpoint
    - Success/failure rates
    - Response time percentiles
    - Error counts
    """

    def __init__(self):
        self._endpoint_stats: Dict[str, EndpointStats] = defaultdict(EndpointStats)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._start_time = datetime.now()

    def record_request(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
    ):
        """
        Record a request metric.

        Args:
            path: Request path (e.g., "/api/clients")
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        endpoint_key = f"{method} {path}"
        self._endpoint_stats[endpoint_key].add_request(duration_ms, status_code)

        # Track errors
        if status_code >= 400:
            error_key = f"{status_code}_{path}"
            self._error_counts[error_key] += 1

    def get_endpoint_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all endpoints.

        Returns:
            Dictionary mapping endpoint to statistics
        """
        return {
            endpoint: {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "success_rate": round(stats.success_rate, 2),
                "avg_duration_ms": round(stats.avg_duration_ms, 2),
                "min_duration_ms": round(stats.min_duration_ms, 2),
                "max_duration_ms": round(stats.max_duration_ms, 2),
                "p95_duration_ms": round(stats.p95_duration_ms, 2),
            }
            for endpoint, stats in self._endpoint_stats.items()
        }

    def get_error_summary(self) -> Dict[str, int]:
        """Get error counts by type"""
        return dict(self._error_counts)

    def get_summary(self) -> Dict:
        """
        Get overall application metrics summary.

        Returns:
            Dictionary with application-wide metrics
        """
        total_requests = sum(stats.total_requests for stats in self._endpoint_stats.values())
        total_errors = sum(stats.failed_requests for stats in self._endpoint_stats.values())
        uptime = datetime.now() - self._start_time

        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(
                (total_errors / total_requests * 100) if total_requests > 0 else 0.0, 2
            ),
            "endpoints_tracked": len(self._endpoint_stats),
        }

    def reset(self):
        """Reset all metrics (for testing)"""
        self._endpoint_stats.clear()
        self._error_counts.clear()
        self._start_time = datetime.now()


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
