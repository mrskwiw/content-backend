"""
Data models for Determine Competitors research tool.

Provides AI-powered competitor discovery and market positioning analysis.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """Competitive threat assessment levels"""

    HIGH = "high"  # Direct competitor, strong overlap
    MEDIUM = "medium"  # Adjacent market, some overlap
    LOW = "low"  # Distant competitor, minimal overlap


class DiscoveredCompetitor(BaseModel):
    """Individual competitor discovered by AI analysis"""

    name: str = Field(..., description="Competitor name/brand")
    market_position: str = Field(..., description="How they position themselves (1-2 sentences)")
    threat_level: ThreatLevel = Field(..., description="Competitive threat assessment")
    strength_areas: List[str] = Field(..., description="2-3 areas where they excel", max_length=5)
    differentiation_opportunity: str = Field(
        ..., description="How to differentiate from them (1 sentence)"
    )
    reasoning: str = Field(..., description="Why they were identified as a competitor")


class DetermineCompetitorsReport(BaseModel):
    """Complete competitor discovery report"""

    business_name: str
    industry: str
    analysis_date: str

    # Results
    primary_competitors: List[DiscoveredCompetitor] = Field(
        default_factory=list, description="Top 3-5 direct competitors"
    )
    emerging_competitors: List[DiscoveredCompetitor] = Field(
        default_factory=list, description="0-2 emerging threats to watch"
    )

    # Insights
    competitive_landscape_summary: str = Field(
        ..., description="2-3 sentence overview of competitive landscape"
    )
    market_gaps: List[str] = Field(
        default_factory=list,
        description="3-5 unmet market needs or positioning opportunities",
    )
    recommended_positioning: str = Field(
        ..., description="Suggested market positioning based on competitive gaps"
    )
