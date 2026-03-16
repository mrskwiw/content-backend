"""Business Report Tool - Output Models

This module defines the Pydantic models for the Business Report research tool.
The tool analyzes company perception, strengths, pain points, and value proposition
using web searches and Google Maps reviews.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class PerceptionInsight(BaseModel):
    """A specific perception insight about the company"""

    category: str = Field(..., description="Category: positive, negative, neutral")
    insight: str = Field(..., description="The perception insight")
    source_count: int = Field(..., description="Number of sources mentioning this", ge=0)
    confidence: str = Field(..., description="Confidence level: High, Medium, Low")


class StrengthRecommendation(BaseModel):
    """A strength to advertise"""

    strength: str = Field(..., description="The strength or differentiator")
    evidence: List[str] = Field(..., description="Supporting evidence from sources")
    recommended_messaging: str = Field(..., description="How to message this strength in marketing")
    target_audience: str = Field(..., description="Who this resonates with")


class PainPoint(BaseModel):
    """A customer pain point identified from reviews and research"""

    pain_point: str = Field(..., description="The pain point description")
    frequency: str = Field(..., description="How often mentioned: High, Medium, Low")
    severity: str = Field(..., description="Impact level: High, Medium, Low")
    customer_quotes: List[str] = Field(
        default_factory=list, description="Direct quotes from customers mentioning this pain point"
    )


class ProblemSolved(BaseModel):
    """A problem the company solves for customers"""

    problem: str = Field(..., description="The problem description")
    solution_approach: str = Field(..., description="How the company solves it")
    value_proposition: str = Field(..., description="The value delivered to customers")
    differentiation: str = Field(..., description="How this differs from competitors")


class BusinessReportOutput(BaseModel):
    """Complete business report analysis output

    This model contains the full analysis of a company including:
    - Perception analysis (how the company is viewed)
    - Strengths to advertise (marketing opportunities)
    - Customer pain points (areas of concern)
    - Problems solved (value propositions)
    """

    # Basic Information
    company_name: str = Field(..., description="Name of the company analyzed")
    location: str = Field(..., description="Location of the company")

    # Perception Analysis
    overall_perception: str = Field(
        ..., description="Summary of overall perception (2-3 sentences)"
    )
    perception_score: int = Field(
        ..., ge=0, le=100, description="Overall perception score from 0-100 (100 = excellent)"
    )
    perception_insights: List[PerceptionInsight] = Field(
        ..., description="Detailed perception insights categorized by sentiment"
    )

    # Strengths to Advertise
    top_strengths: List[StrengthRecommendation] = Field(
        ..., description="Top 3-5 strengths with marketing recommendations"
    )

    # Pain Points
    customer_pain_points: List[PainPoint] = Field(
        ..., description="Key customer pain points identified from research"
    )

    # Problems Solved
    problems_solved: List[ProblemSolved] = Field(
        ..., description="Problems the company solves with value propositions"
    )

    # Source Data Metadata
    web_sources_analyzed: int = Field(..., ge=0, description="Number of web sources analyzed")
    reviews_analyzed: int = Field(..., ge=0, description="Number of reviews analyzed")
    average_rating: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="Average rating from Google Maps (if available)"
    )
    total_reviews: Optional[int] = Field(
        None, ge=0, description="Total number of reviews on Google Maps (if available)"
    )

    # Analysis Metadata
    analysis_date: str = Field(..., description="Date of analysis (ISO 8601 format)")
    confidence_level: str = Field(
        ..., description="Overall confidence in analysis: High, Medium, Low"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_name": "Acme Coffee Co",
                "location": "Seattle, WA",
                "overall_perception": "Premium local coffee shop known for exceptional quality and strong community ties. Customers consistently praise the artisanal approach and personalized service, though some mention wait times during peak hours.",
                "perception_score": 82,
                "perception_insights": [
                    {
                        "category": "positive",
                        "insight": "Consistently praised for high-quality, locally-roasted beans",
                        "source_count": 45,
                        "confidence": "High",
                    },
                    {
                        "category": "positive",
                        "insight": "Strong reputation for knowledgeable, friendly baristas",
                        "source_count": 38,
                        "confidence": "High",
                    },
                    {
                        "category": "negative",
                        "insight": "Long wait times during morning rush hours",
                        "source_count": 22,
                        "confidence": "Medium",
                    },
                    {
                        "category": "neutral",
                        "insight": "Higher prices than chain competitors",
                        "source_count": 15,
                        "confidence": "Medium",
                    },
                ],
                "top_strengths": [
                    {
                        "strength": "Local sourcing and artisanal roasting",
                        "evidence": [
                            "Mentioned in 78% of positive reviews",
                            "Featured in Seattle Times coffee guide",
                            "Multiple awards for roasting quality",
                        ],
                        "recommended_messaging": "Seattle's premier locally-roasted coffee experience - beans roasted fresh daily in-house",
                        "target_audience": "Coffee enthusiasts, local food supporters, quality-conscious consumers",
                    },
                    {
                        "strength": "Knowledgeable staff and coffee education",
                        "evidence": [
                            "Baristas frequently praised for expertise",
                            "Offers brewing classes and tastings",
                            "Staff can explain origin and flavor profiles",
                        ],
                        "recommended_messaging": "Learn from passionate coffee experts - our baristas are certified in coffee science",
                        "target_audience": "Coffee learners, specialty coffee newcomers, experience seekers",
                    },
                    {
                        "strength": "Community gathering space",
                        "evidence": [
                            "Hosts local events and artist showcases",
                            "Customers mention 'neighborhood feel'",
                            "Partners with local businesses",
                        ],
                        "recommended_messaging": "More than coffee - your neighborhood's living room where community connects",
                        "target_audience": "Local residents, remote workers, community-minded consumers",
                    },
                ],
                "customer_pain_points": [
                    {
                        "pain_point": "Long wait times during morning rush",
                        "frequency": "High",
                        "severity": "Medium",
                        "customer_quotes": [
                            "Always a line but worth the wait",
                            "Wish they had more staff in the mornings",
                            "Great coffee but plan for 10-15 min wait at 8am",
                        ],
                    },
                    {
                        "pain_point": "Limited seating during busy periods",
                        "frequency": "Medium",
                        "severity": "Low",
                        "customer_quotes": [
                            "Hard to find a seat on weekends",
                            "Popular spot so seating is tight",
                        ],
                    },
                    {
                        "pain_point": "Higher prices than chain alternatives",
                        "frequency": "Medium",
                        "severity": "Low",
                        "customer_quotes": [
                            "More expensive than Starbucks but quality shows",
                            "Premium pricing but you get what you pay for",
                        ],
                    },
                ],
                "problems_solved": [
                    {
                        "problem": "Finding truly fresh, locally-roasted coffee in Seattle",
                        "solution_approach": "Daily small-batch roasting on-site with transparent sourcing",
                        "value_proposition": "Coffee roasted within 48 hours, guaranteed peak freshness",
                        "differentiation": "Most local competitors buy pre-roasted beans from distributors",
                    },
                    {
                        "problem": "Lack of coffee knowledge prevents optimal brewing at home",
                        "solution_approach": "Free brewing workshops, one-on-one consultations, detailed brew guides",
                        "value_proposition": "Educational experience that empowers customers to brew better coffee",
                        "differentiation": "Chain stores don't invest in customer education",
                    },
                    {
                        "problem": "Need for authentic community gathering space",
                        "solution_approach": "Host local events, showcase local artists, create welcoming environment",
                        "value_proposition": "Third place that strengthens neighborhood connections",
                        "differentiation": "Corporate chains lack genuine local community integration",
                    },
                ],
                "web_sources_analyzed": 12,
                "reviews_analyzed": 156,
                "average_rating": 4.6,
                "total_reviews": 156,
                "analysis_date": "2026-03-16",
                "confidence_level": "High",
            }
        }
    )


# Convenience function for creating analysis date
def get_analysis_date() -> str:
    """Get current date in ISO 8601 format for analysis_date field"""
    return datetime.now().date().isoformat()
