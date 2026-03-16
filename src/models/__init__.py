"""Pydantic data models for content generation

Contains:
- ClientBrief: Structured client information
- Post: Generated post with metadata
- Template: Post template structure
- QAReport: Quality validation results
- VoiceGuide: Brand voice guidelines
- KeywordStrategy: SEO keyword recommendations
- QualityProfile: Quality threshold configuration
- PostingSchedule: Content calendar and scheduling
- BusinessReportOutput: Business report analysis (research tool)
"""

# Research tool models
from .business_report_models import (
    BusinessReportOutput,
    PerceptionInsight,
    StrengthRecommendation,
    PainPoint,
    ProblemSolved,
    get_analysis_date,
)

__all__ = [
    "BusinessReportOutput",
    "PerceptionInsight",
    "StrengthRecommendation",
    "PainPoint",
    "ProblemSolved",
    "get_analysis_date",
]
