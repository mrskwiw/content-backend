"""
Health check endpoints for system integrations and services.

Provides status checks for external integrations like Google Trends (pytrends),
Anthropic API, and other dependencies.
"""

from fastapi import APIRouter
from typing import Dict, Any
import time

from backend.utils.logger import logger

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/pytrends")
async def check_pytrends() -> Dict[str, Any]:
    """
    Test Google Trends (pytrends) connectivity.

    Returns:
        Dict with status, latency, and version info
    """
    start_time = time.time()

    try:
        from pytrends.request import TrendReq
        import urllib3

        # Try to create a pytrends client
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(5, 10))

        # Quick test query with a very popular term
        pytrends.build_payload(["python"], timeframe="now 7-d", geo="")
        interest_df = pytrends.interest_over_time()

        elapsed = time.time() - start_time

        if not interest_df.empty:
            return {
                "status": "connected",
                "message": "Google Trends API is accessible",
                "latency_ms": round(elapsed * 1000, 2),
                "pytrends_version": "4.9.2",
                "urllib3_version": urllib3.__version__,
                "test_query": "python",
                "data_points": len(interest_df),
            }
        else:
            return {
                "status": "warning",
                "message": "Google Trends responded but returned no data",
                "latency_ms": round(elapsed * 1000, 2),
            }

    except ImportError as e:
        logger.error(f"Pytrends not installed: {e}")
        return {
            "status": "error",
            "message": "pytrends library not installed",
            "error": str(e),
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Pytrends connectivity test failed: {e}")
        return {
            "status": "error",
            "message": "Failed to connect to Google Trends",
            "error": str(e),
            "latency_ms": round(elapsed * 1000, 2),
        }


@router.get("/anthropic")
async def check_anthropic() -> Dict[str, Any]:
    """
    Test Anthropic API connectivity.

    Returns:
        Dict with status and API key validity
    """
    try:
        from backend.config import settings

        if not settings.ANTHROPIC_API_KEY:
            return {
                "status": "error",
                "message": "ANTHROPIC_API_KEY not configured",
            }

        if not settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
            return {
                "status": "warning",
                "message": "API key format appears invalid",
            }

        # Don't make an actual API call to avoid costs
        # Just verify the key is configured
        return {
            "status": "configured",
            "message": "Anthropic API key is configured",
            "model": settings.ANTHROPIC_MODEL,
        }

    except Exception as e:
        logger.error(f"Anthropic API check failed: {e}")
        return {
            "status": "error",
            "message": "Failed to check Anthropic API",
            "error": str(e),
        }


@router.get("/system")
async def check_system() -> Dict[str, Any]:
    """
    Overall system health check.

    Returns:
        Dict with status of all integrations
    """
    pytrends_status = await check_pytrends()
    anthropic_status = await check_anthropic()

    all_healthy = pytrends_status["status"] in ["connected", "configured"] and anthropic_status[
        "status"
    ] in ["connected", "configured"]

    return {
        "status": "healthy" if all_healthy else "degraded",
        "integrations": {
            "pytrends": pytrends_status,
            "anthropic": anthropic_status,
        },
    }
