"""
Google Trends Service.

Provides integration with Google Trends API via pytrends for keyword research
and optimization. All search results are stored in the database for historical
tracking and analysis.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import statistics

from sqlalchemy.orm import Session

from backend.models.trends import (
    TrendsSearch,
    TrendsInterestData,
    TrendsRelatedQuery,
    TrendsKeywordInsight,
)
from backend.utils.logger import logger


class GoogleTrendsService:
    """
    Service for Google Trends data retrieval and storage.

    Features:
    - Search interest over time for keywords
    - Related queries (top and rising)
    - Historical data storage in database
    - Keyword insights and recommendations
    - Rate limiting to avoid Google blocks
    """

    # Timeframe options
    TIMEFRAMES = {
        "past_hour": "now 1-H",
        "past_4_hours": "now 4-H",
        "past_day": "now 1-d",
        "past_week": "now 7-d",
        "past_month": "today 1-m",
        "past_3_months": "today 3-m",
        "past_12_months": "today 12-m",
        "past_5_years": "today 5-y",
        "all_time": "all",
    }

    # Common category IDs
    CATEGORIES = {
        "all": 0,
        "arts_entertainment": 3,
        "autos_vehicles": 47,
        "beauty_fitness": 44,
        "books_literature": 22,
        "business_industrial": 12,
        "computers_electronics": 5,
        "finance": 7,
        "food_drink": 71,
        "games": 8,
        "health": 45,
        "hobbies_leisure": 64,
        "home_garden": 11,
        "internet_telecom": 13,
        "jobs_education": 958,
        "law_government": 19,
        "news": 16,
        "online_communities": 299,
        "people_society": 14,
        "pets_animals": 66,
        "real_estate": 29,
        "reference": 533,
        "science": 174,
        "shopping": 18,
        "sports": 20,
        "travel": 67,
    }

    def __init__(self):
        """Initialize the Google Trends service."""
        self._pytrends = None
        self._last_request_time = None
        self._min_request_interval = 2.0  # Seconds between requests to avoid rate limiting

    @property
    def pytrends(self):
        """Lazy-load pytrends client."""
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq

                self._pytrends = TrendReq(
                    hl="en-US",
                    tz=360,
                    timeout=(10, 25),
                    retries=2,
                    backoff_factor=0.5,
                )
                logger.info("PyTrends client initialized")
            except ImportError:
                logger.error("pytrends not installed. Run: pip install pytrends")
                raise ImportError(
                    "pytrends is required for Google Trends integration. "
                    "Install with: pip install pytrends"
                )
        return self._pytrends

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        import time

        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def search_interest_over_time(
        self,
        db: Session,
        keywords: List[str],
        user_id: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe: str = "past_12_months",
        geo: str = "",
        category: str = "all",
    ) -> Dict[str, Any]:
        """
        Search Google Trends for interest over time data.

        Args:
            db: Database session
            keywords: List of keywords to search (max 5)
            user_id: User performing the search
            client_id: Optional client association
            project_id: Optional project association
            timeframe: Time range (use TIMEFRAMES keys)
            geo: Geographic region code (e.g., "US", "GB", empty for worldwide)
            category: Category name (use CATEGORIES keys)

        Returns:
            Dictionary with search results and metadata
        """
        # Validate inputs
        if not keywords or len(keywords) > 5:
            return {
                "success": False,
                "error": "Must provide 1-5 keywords",
            }

        # Resolve timeframe and category
        tf = self.TIMEFRAMES.get(timeframe, timeframe)
        cat = self.CATEGORIES.get(category, 0)

        # Create search record
        search_id = f"ts-{uuid.uuid4().hex[:12]}"
        search = TrendsSearch(
            id=search_id,
            user_id=user_id,
            client_id=client_id,
            project_id=project_id,
            keywords=keywords,
            timeframe=tf,
            geo=geo,
            category=cat,
            search_type="interest_over_time",
            status="pending",
        )
        db.add(search)
        db.commit()

        try:
            # Rate limit
            self._rate_limit()

            # Build payload and fetch data
            self.pytrends.build_payload(
                keywords,
                timeframe=tf,
                geo=geo,
                cat=cat,
            )

            interest_df = self.pytrends.interest_over_time()

            if interest_df.empty:
                search.status = "completed"
                search.error_message = "No data returned for these keywords"
                db.commit()
                return {
                    "success": True,
                    "search_id": search_id,
                    "keywords": keywords,
                    "data_points": 0,
                    "message": "No data available for these keywords in the specified timeframe",
                }

            # Store interest data
            data_points = []
            for date_idx, row in interest_df.iterrows():
                for keyword in keywords:
                    if keyword in row:
                        point_id = f"tid-{uuid.uuid4().hex[:12]}"
                        is_partial = row.get("isPartial", False) if "isPartial" in row else False

                        data_point = TrendsInterestData(
                            id=point_id,
                            search_id=search_id,
                            keyword=keyword,
                            date=date_idx.to_pydatetime(),
                            interest_value=int(row[keyword]),
                            is_partial=bool(is_partial),
                        )
                        db.add(data_point)
                        data_points.append(
                            {
                                "keyword": keyword,
                                "date": date_idx.isoformat(),
                                "interest": int(row[keyword]),
                            }
                        )

            search.status = "completed"
            db.commit()

            logger.info(f"Trends search {search_id}: {len(data_points)} data points for {keywords}")

            return {
                "success": True,
                "search_id": search_id,
                "keywords": keywords,
                "timeframe": tf,
                "geo": geo or "worldwide",
                "data_points": len(data_points),
                "sample_data": data_points[:10],  # First 10 points as sample
            }

        except Exception as e:
            search.status = "failed"
            search.error_message = str(e)
            db.commit()
            logger.error(f"Trends search failed: {e}")
            return {
                "success": False,
                "search_id": search_id,
                "error": str(e),
            }

    def search_related_queries(
        self,
        db: Session,
        keywords: List[str],
        user_id: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe: str = "past_12_months",
        geo: str = "",
        category: str = "all",
    ) -> Dict[str, Any]:
        """
        Search Google Trends for related queries.

        Returns both "top" (most popular) and "rising" (fastest growing) queries.

        Args:
            db: Database session
            keywords: List of keywords to search (max 5)
            user_id: User performing the search
            client_id: Optional client association
            project_id: Optional project association
            timeframe: Time range
            geo: Geographic region
            category: Category name

        Returns:
            Dictionary with related queries
        """
        if not keywords or len(keywords) > 5:
            return {"success": False, "error": "Must provide 1-5 keywords"}

        tf = self.TIMEFRAMES.get(timeframe, timeframe)
        cat = self.CATEGORIES.get(category, 0)

        # Create search record
        search_id = f"ts-{uuid.uuid4().hex[:12]}"
        search = TrendsSearch(
            id=search_id,
            user_id=user_id,
            client_id=client_id,
            project_id=project_id,
            keywords=keywords,
            timeframe=tf,
            geo=geo,
            category=cat,
            search_type="related_queries",
            status="pending",
        )
        db.add(search)
        db.commit()

        try:
            self._rate_limit()

            self.pytrends.build_payload(keywords, timeframe=tf, geo=geo, cat=cat)
            related = self.pytrends.related_queries()

            all_queries = []
            for keyword in keywords:
                if keyword not in related:
                    continue

                kw_data = related[keyword]

                # Process top queries
                if kw_data.get("top") is not None and not kw_data["top"].empty:
                    for _, row in kw_data["top"].iterrows():
                        query_id = f"trq-{uuid.uuid4().hex[:12]}"
                        query = TrendsRelatedQuery(
                            id=query_id,
                            search_id=search_id,
                            source_keyword=keyword,
                            query=row["query"],
                            query_type="top",
                            value=float(row["value"]) if "value" in row else None,
                        )
                        db.add(query)
                        all_queries.append(
                            {
                                "source": keyword,
                                "query": row["query"],
                                "type": "top",
                                "value": row.get("value"),
                            }
                        )

                # Process rising queries
                if kw_data.get("rising") is not None and not kw_data["rising"].empty:
                    for _, row in kw_data["rising"].iterrows():
                        query_id = f"trq-{uuid.uuid4().hex[:12]}"
                        value = row.get("value")
                        # Rising values can be "Breakout" string
                        if isinstance(value, str):
                            value = 1000.0 if value == "Breakout" else None
                        query = TrendsRelatedQuery(
                            id=query_id,
                            search_id=search_id,
                            source_keyword=keyword,
                            query=row["query"],
                            query_type="rising",
                            value=float(value) if value else None,
                        )
                        db.add(query)
                        all_queries.append(
                            {
                                "source": keyword,
                                "query": row["query"],
                                "type": "rising",
                                "value": row.get("value"),
                            }
                        )

            search.status = "completed"
            db.commit()

            logger.info(f"Related queries search {search_id}: {len(all_queries)} queries found")

            return {
                "success": True,
                "search_id": search_id,
                "keywords": keywords,
                "total_queries": len(all_queries),
                "top_queries": [q for q in all_queries if q["type"] == "top"][:20],
                "rising_queries": [q for q in all_queries if q["type"] == "rising"][:20],
            }

        except Exception as e:
            search.status = "failed"
            search.error_message = str(e)
            db.commit()
            logger.error(f"Related queries search failed: {e}")
            return {"success": False, "search_id": search_id, "error": str(e)}

    def compute_keyword_insights(
        self,
        db: Session,
        keyword: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute insights for a keyword based on stored trends data.

        Analyzes historical search data to determine:
        - Trend direction (rising/declining/stable/seasonal)
        - Average/peak interest levels
        - Seasonality patterns
        - Content recommendations

        Args:
            db: Database session
            keyword: Keyword to analyze
            client_id: Optional client filter
            project_id: Optional project filter

        Returns:
            Dictionary with keyword insights
        """
        # Get all interest data for this keyword
        query = db.query(TrendsInterestData).filter(TrendsInterestData.keyword == keyword)

        # Apply filters if provided
        if client_id or project_id:
            query = query.join(TrendsSearch)
            if client_id:
                query = query.filter(TrendsSearch.client_id == client_id)
            if project_id:
                query = query.filter(TrendsSearch.project_id == project_id)

        data_points = query.order_by(TrendsInterestData.date.asc()).all()

        if not data_points:
            return {
                "success": False,
                "error": f"No trends data found for keyword '{keyword}'",
            }

        # Calculate metrics
        values = [dp.interest_value for dp in data_points]

        avg_interest = statistics.mean(values)
        max_interest = max(values)
        min_interest = min(values)

        # Calculate trend direction using simple linear regression
        n = len(values)
        if n >= 2:
            x_mean = (n - 1) / 2
            y_mean = avg_interest
            numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
            trend_strength = slope / (max_interest - min_interest + 1)  # Normalize
        else:
            slope = 0
            trend_strength = 0

        # Determine trend direction
        if abs(trend_strength) < 0.1:
            trend_direction = "stable"
        elif trend_strength > 0.3:
            trend_direction = "rising"
        elif trend_strength < -0.3:
            trend_direction = "declining"
        else:
            trend_direction = "slight_" + ("rising" if trend_strength > 0 else "declining")

        # Check for seasonality (monthly patterns)
        monthly_avg = {}
        for dp in data_points:
            month = dp.date.month
            if month not in monthly_avg:
                monthly_avg[month] = []
            monthly_avg[month].append(dp.interest_value)

        monthly_means = {m: statistics.mean(vals) for m, vals in monthly_avg.items()}

        # Detect seasonality if some months are significantly higher
        if monthly_means:
            overall_mean = statistics.mean(monthly_means.values())
            peak_months = [m for m, v in monthly_means.items() if v > overall_mean * 1.3]
            is_seasonal = len(peak_months) > 0 and len(peak_months) < 6
        else:
            is_seasonal = False
            peak_months = []

        # Generate content recommendation
        if trend_direction == "rising":
            recommendation = f"High priority: '{keyword}' is trending up. Create content now to capture growing interest."
        elif trend_direction == "declining":
            recommendation = f"Lower priority: '{keyword}' interest is declining. Consider related rising topics instead."
        elif is_seasonal:
            month_names = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            peak_names = [month_names[m - 1] for m in peak_months]
            recommendation = (
                f"Seasonal keyword: Plan content for peak months ({', '.join(peak_names)})."
            )
        else:
            recommendation = (
                f"Stable keyword: '{keyword}' has consistent interest. Good for evergreen content."
            )

        # Calculate priority score (0-100)
        priority_score = min(100, (avg_interest * 0.5) + (max(0, trend_strength * 50) + 25))

        # Create or update insight record
        existing = (
            db.query(TrendsKeywordInsight)
            .filter(
                TrendsKeywordInsight.keyword == keyword,
                TrendsKeywordInsight.client_id == client_id,
                TrendsKeywordInsight.project_id == project_id,
            )
            .first()
        )

        if existing:
            insight = existing
        else:
            insight = TrendsKeywordInsight(
                id=f"tki-{uuid.uuid4().hex[:12]}",
                client_id=client_id,
                project_id=project_id,
                keyword=keyword,
            )
            db.add(insight)

        insight.avg_interest = avg_interest
        insight.max_interest = max_interest
        insight.min_interest = min_interest
        insight.trend_direction = trend_direction
        insight.trend_strength = trend_strength
        insight.is_seasonal = is_seasonal
        insight.peak_months = peak_months if peak_months else None
        insight.content_recommendation = recommendation
        insight.priority_score = priority_score
        insight.data_points_count = len(data_points)
        insight.last_updated = datetime.utcnow()

        db.commit()

        logger.info(
            f"Computed insights for '{keyword}': {trend_direction}, priority={priority_score:.1f}"
        )

        return {
            "success": True,
            "keyword": keyword,
            "insight_id": insight.id,
            "metrics": {
                "avg_interest": round(avg_interest, 1),
                "max_interest": max_interest,
                "min_interest": min_interest,
                "data_points": len(data_points),
            },
            "trend": {
                "direction": trend_direction,
                "strength": round(trend_strength, 3),
            },
            "seasonality": {
                "is_seasonal": is_seasonal,
                "peak_months": peak_months,
            },
            "recommendation": recommendation,
            "priority_score": round(priority_score, 1),
        }

    def get_search_history(
        self,
        db: Session,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get trends search history with optional filters.

        Args:
            db: Database session
            user_id: Filter by user
            client_id: Filter by client
            project_id: Filter by project
            limit: Maximum results

        Returns:
            Dictionary with search history
        """
        query = db.query(TrendsSearch).order_by(TrendsSearch.created_at.desc())

        if user_id:
            query = query.filter(TrendsSearch.user_id == user_id)
        if client_id:
            query = query.filter(TrendsSearch.client_id == client_id)
        if project_id:
            query = query.filter(TrendsSearch.project_id == project_id)

        searches = query.limit(limit).all()

        return {
            "success": True,
            "count": len(searches),
            "searches": [
                {
                    "id": s.id,
                    "keywords": s.keywords,
                    "search_type": s.search_type,
                    "timeframe": s.timeframe,
                    "geo": s.geo or "worldwide",
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in searches
            ],
        }

    def get_keyword_insights(
        self,
        db: Session,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        min_priority: float = 0,
    ) -> Dict[str, Any]:
        """
        Get all keyword insights with optional filters.

        Args:
            db: Database session
            client_id: Filter by client
            project_id: Filter by project
            min_priority: Minimum priority score filter

        Returns:
            Dictionary with keyword insights
        """
        query = db.query(TrendsKeywordInsight)

        if client_id:
            query = query.filter(TrendsKeywordInsight.client_id == client_id)
        if project_id:
            query = query.filter(TrendsKeywordInsight.project_id == project_id)
        if min_priority > 0:
            query = query.filter(TrendsKeywordInsight.priority_score >= min_priority)

        query = query.order_by(TrendsKeywordInsight.priority_score.desc())
        insights = query.all()

        return {
            "success": True,
            "count": len(insights),
            "insights": [
                {
                    "id": i.id,
                    "keyword": i.keyword,
                    "trend_direction": i.trend_direction,
                    "priority_score": i.priority_score,
                    "avg_interest": i.avg_interest,
                    "is_seasonal": i.is_seasonal,
                    "recommendation": i.content_recommendation,
                    "last_updated": i.last_updated.isoformat() if i.last_updated else None,
                }
                for i in insights
            ],
        }


# Singleton instance
trends_service = GoogleTrendsService()
