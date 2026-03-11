"""
Cost API Response Schemas

Pydantic schemas for token usage and cost reporting endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCostSummary(BaseModel):
    """Cost summary for a single project"""

    project_id: str
    project_name: str
    total_runs: int
    total_posts: int
    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_generation_cost_usd: float
    total_research_tools: int
    total_research_cost_usd: float
    total_cost_usd: float
    cost_per_post: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RunCostBreakdown(BaseModel):
    """Detailed cost breakdown for a single run"""

    run_id: str
    project_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: float
    estimated_cost_usd: Optional[float] = None
    total_posts: int
    posts_with_token_data: int
    avg_cost_per_post: Optional[float] = None
    cache_savings_usd: Optional[float] = Field(
        None, description="Estimated cost savings from prompt caching"
    )

    model_config = ConfigDict(from_attributes=True)


class CostTrend(BaseModel):
    """Daily cost data point for trends"""

    date: str  # ISO date string (YYYY-MM-DD)
    cost_usd: float


class UserCostSummary(BaseModel):
    """Cost summary across all user's projects"""

    user_id: str
    period_days: int = Field(description="Number of days analyzed")
    total_projects: int
    total_runs: int
    total_input_tokens: int
    total_output_tokens: int
    total_generation_cost_usd: float
    total_research_tools: int
    total_research_cost_usd: float
    total_cost_usd: float
    top_projects: List[Dict[str, Any]] = Field(
        description="Top 5 most expensive projects",
        default_factory=list,
    )
    cost_trend: List[CostTrend] = Field(
        description="Daily cost trend (last 7 days)",
        default_factory=list,
    )

    model_config = ConfigDict(from_attributes=True)


class ResearchCostSummary(BaseModel):
    """Research tool cost summary for a client"""

    client_id: str
    client_name: str
    total_research_tools: int = Field(description="Total number of research tools executed")
    total_business_price_usd: float = Field(
        description="Total business model price ($300-600 per tool)"
    )
    total_actual_cost_usd: float = Field(description="Total actual API cost")
    price_difference_usd: float = Field(description="Business price - actual cost (profit margin)")
    tools_breakdown: List[Dict[str, Any]] = Field(
        description="Per-tool cost breakdown",
        default_factory=list,
    )

    model_config = ConfigDict(from_attributes=True)
