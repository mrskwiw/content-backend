"""
Google Trends data models.

Stores search results from Google Trends for keyword optimization and historical tracking.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class TrendsSearch(Base):
    """
    Record of a Google Trends search.

    Each search can contain multiple keywords and stores metadata about the search.
    """

    __tablename__ = "trends_searches"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    # Search parameters
    keywords = Column(JSON, nullable=False)  # List of keywords searched
    timeframe = Column(String, default="today 12-m")  # e.g., "today 12-m", "today 3-m"
    geo = Column(String, default="")  # Geographic region (empty = worldwide)
    category = Column(Integer, default=0)  # Google Trends category ID

    # Search metadata
    search_type = Column(
        String, default="interest_over_time"
    )  # interest_over_time, related_queries, related_topics
    status = Column(String, default="completed")  # pending, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("backend.models.user.User", foreign_keys=[user_id])
    client = relationship("backend.models.client.Client", foreign_keys=[client_id])
    project = relationship("backend.models.project.Project", foreign_keys=[project_id])
    results = relationship(
        "TrendsInterestData",
        back_populates="search",
        cascade="all, delete-orphan",
    )
    related_queries = relationship(
        "TrendsRelatedQuery",
        back_populates="search",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<TrendsSearch {self.id} keywords={self.keywords}>"


class TrendsInterestData(Base):
    """
    Interest over time data points from Google Trends.

    Stores the relative search interest (0-100) for each keyword at each time point.
    """

    __tablename__ = "trends_interest_data"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    search_id = Column(String, ForeignKey("trends_searches.id"), nullable=False, index=True)

    # Data point
    keyword = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    interest_value = Column(Integer, nullable=False)  # 0-100 relative interest
    is_partial = Column(Boolean, default=False)  # Partial data point (incomplete period)

    # Relationship
    search = relationship("TrendsSearch", back_populates="results")

    def __repr__(self):
        return f"<TrendsInterestData {self.keyword} {self.date}: {self.interest_value}>"


class TrendsRelatedQuery(Base):
    """
    Related queries from Google Trends.

    Stores both "top" (most popular) and "rising" (fastest growing) related queries.
    """

    __tablename__ = "trends_related_queries"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    search_id = Column(String, ForeignKey("trends_searches.id"), nullable=False, index=True)

    # Query data
    source_keyword = Column(String, nullable=False, index=True)  # The keyword this is related to
    query = Column(String, nullable=False)  # The related query text
    query_type = Column(String, nullable=False)  # "top" or "rising"
    value = Column(Float, nullable=True)  # Interest value (top) or % increase (rising)

    # Relationship
    search = relationship("TrendsSearch", back_populates="related_queries")

    def __repr__(self):
        return f"<TrendsRelatedQuery {self.source_keyword} -> {self.query} ({self.query_type})>"


class TrendsKeywordInsight(Base):
    """
    Aggregated keyword insights derived from trends data.

    Provides actionable insights for content optimization based on trends analysis.
    """

    __tablename__ = "trends_keyword_insights"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    # Keyword data
    keyword = Column(String, nullable=False, index=True)

    # Trend metrics (computed from interest data)
    avg_interest = Column(Float, nullable=True)  # Average interest over period
    max_interest = Column(Float, nullable=True)  # Peak interest
    min_interest = Column(Float, nullable=True)  # Lowest interest
    trend_direction = Column(String, nullable=True)  # "rising", "declining", "stable", "seasonal"
    trend_strength = Column(Float, nullable=True)  # -1.0 to 1.0 trend coefficient

    # Seasonality
    is_seasonal = Column(Boolean, default=False)
    peak_months = Column(JSON, nullable=True)  # List of months with peak interest

    # Recommendations
    content_recommendation = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=True)  # 0-100 priority for content creation

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    data_points_count = Column(Integer, default=0)

    # Relationships
    client = relationship("backend.models.client.Client", foreign_keys=[client_id])
    project = relationship("backend.models.project.Project", foreign_keys=[project_id])

    def __repr__(self):
        return f"<TrendsKeywordInsight {self.keyword} trend={self.trend_direction}>"
