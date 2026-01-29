"""
Google Trends API endpoints.

Provides endpoints for searching Google Trends, retrieving related queries,
and managing keyword insights for content optimization.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.auth_dependency import get_current_user
from backend.models import User
from backend.services.trends_service import trends_service
from backend.utils.http_rate_limiter import standard_limiter
from backend.utils.logger import logger

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class TrendsSearchRequest(BaseModel):
    """Request for trends search."""

    keywords: List[str] = Field(..., min_length=1, max_length=5)
    timeframe: str = Field(default="past_12_months")
    geo: str = Field(default="")
    category: str = Field(default="all")
    client_id: Optional[str] = None
    project_id: Optional[str] = None


class TrendsSearchResponse(BaseModel):
    """Response for trends search."""

    success: bool
    search_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    timeframe: Optional[str] = None
    geo: Optional[str] = None
    data_points: Optional[int] = None
    sample_data: Optional[List[dict]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class RelatedQueriesResponse(BaseModel):
    """Response for related queries search."""

    success: bool
    search_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    total_queries: Optional[int] = None
    top_queries: Optional[List[dict]] = None
    rising_queries: Optional[List[dict]] = None
    error: Optional[str] = None


class KeywordInsightRequest(BaseModel):
    """Request for keyword insight computation."""

    keyword: str
    client_id: Optional[str] = None
    project_id: Optional[str] = None


class KeywordInsightResponse(BaseModel):
    """Response for keyword insights."""

    success: bool
    keyword: Optional[str] = None
    insight_id: Optional[str] = None
    metrics: Optional[dict] = None
    trend: Optional[dict] = None
    seasonality: Optional[dict] = None
    recommendation: Optional[str] = None
    priority_score: Optional[float] = None
    error: Optional[str] = None


class SearchHistoryResponse(BaseModel):
    """Response for search history."""

    success: bool
    count: int
    searches: List[dict]


class InsightsListResponse(BaseModel):
    """Response for insights list."""

    success: bool
    count: int
    insights: List[dict]


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/search/interest", response_model=TrendsSearchResponse)
@standard_limiter.limit("30/hour")
async def search_interest_over_time(
    request: Request,
    search_request: TrendsSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search Google Trends for interest over time data.

    Searches for up to 5 keywords and returns historical interest data.
    Results are stored in the database for future analysis.

    Rate limit: 30 requests per hour (Google Trends rate limiting)
    """
    try:
        logger.info(f"Trends search: {search_request.keywords} by user {current_user.id}")

        result = trends_service.search_interest_over_time(
            db=db,
            keywords=search_request.keywords,
            user_id=current_user.id,
            client_id=search_request.client_id,
            project_id=search_request.project_id,
            timeframe=search_request.timeframe,
            geo=search_request.geo,
            category=search_request.category,
        )

        return result

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Trends integration not available. Install pytrends: pip install pytrends",
        )
    except Exception as e:
        logger.error(f"Trends search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trends search failed: {str(e)}",
        )


@router.post("/search/related", response_model=RelatedQueriesResponse)
@standard_limiter.limit("30/hour")
async def search_related_queries(
    request: Request,
    search_request: TrendsSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search Google Trends for related queries.

    Returns both "top" (most popular) and "rising" (fastest growing) related queries.
    Results are stored in the database for keyword expansion.

    Rate limit: 30 requests per hour
    """
    try:
        logger.info(f"Related queries search: {search_request.keywords} by user {current_user.id}")

        result = trends_service.search_related_queries(
            db=db,
            keywords=search_request.keywords,
            user_id=current_user.id,
            client_id=search_request.client_id,
            project_id=search_request.project_id,
            timeframe=search_request.timeframe,
            geo=search_request.geo,
            category=search_request.category,
        )

        return result

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Trends integration not available. Install pytrends.",
        )
    except Exception as e:
        logger.error(f"Related queries search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Related queries search failed: {str(e)}",
        )


@router.post("/insights/compute", response_model=KeywordInsightResponse)
@standard_limiter.limit("100/hour")
async def compute_keyword_insight(
    request: Request,
    insight_request: KeywordInsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute insights for a keyword from stored trends data.

    Analyzes historical data to determine trend direction, seasonality,
    and content recommendations.

    Rate limit: 100 requests per hour (no external API calls)
    """
    try:
        result = trends_service.compute_keyword_insights(
            db=db,
            keyword=insight_request.keyword,
            client_id=insight_request.client_id,
            project_id=insight_request.project_id,
        )

        return result

    except Exception as e:
        logger.error(f"Insight computation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insight computation failed: {str(e)}",
        )


@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    request: Request,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get trends search history.

    Returns previous searches with optional filtering by client or project.
    """
    try:
        result = trends_service.get_search_history(
            db=db,
            user_id=current_user.id,
            client_id=client_id,
            project_id=project_id,
            limit=limit,
        )

        return result

    except Exception as e:
        logger.error(f"Search history error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search history: {str(e)}",
        )


@router.get("/insights", response_model=InsightsListResponse)
async def get_keyword_insights(
    request: Request,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
    min_priority: float = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all keyword insights.

    Returns computed insights with optional filtering and minimum priority threshold.
    """
    try:
        result = trends_service.get_keyword_insights(
            db=db,
            client_id=client_id,
            project_id=project_id,
            min_priority=min_priority,
        )

        return result

    except Exception as e:
        logger.error(f"Get insights error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}",
        )


@router.get("/timeframes")
async def get_available_timeframes():
    """Get available timeframe options for trends searches."""
    return {
        "timeframes": trends_service.TIMEFRAMES,
        "default": "past_12_months",
    }


@router.get("/categories")
async def get_available_categories():
    """Get available category options for trends searches."""
    return {
        "categories": trends_service.CATEGORIES,
        "default": "all",
    }
