"""
Credit pricing configuration.

Defines credit costs for all content types and research tools.
Costs are based on human labor replacement value and complexity.

Pricing Philosophy:
- Blog posts: 20 credits (replaces 2-3 hours of writing)
- Research tools: 50-150 credits based on labor savings
  - 50 credits: Replaces 3-4 hours of work
  - 75 credits: Replaces 4-6 hours of work
  - 100 credits: Replaces 6-8 hours of work
  - 150 credits: Replaces 8-12 hours of work
"""

# Content generation costs
CONTENT_COSTS = {
    "blog_post": 20,  # Long-form blog content (500-1500 words)
}

# Research tool costs (50-150 credits based on labor replacement)
RESEARCH_TOOL_COSTS = {
    # Light research (50 credits ~ $100-125)
    "platform_strategy": 50,  # Platform-specific recommendations (3-4 hours)
    "content_calendar": 50,  # 30-day content calendar generation (3-4 hours)
    "market_trends": 50,  # Industry trends and insights (3-4 hours)
    # Medium research (75 credits ~ $150-187.50)
    "brand_archetype": 75,  # Brand personality analysis (4-6 hours)
    "audience_research": 75,  # Demographic and psychographic profiling (4-6 hours)
    "content_audit": 75,  # Content performance analysis (4-6 hours)
    # Heavy research (100 credits ~ $200-250)
    "voice_analysis": 100,  # Brand voice documentation (6-8 hours)
    "competitive_analysis": 100,  # Competitor content strategy (6-8 hours)
    "content_gap": 100,  # Gap analysis and opportunities (6-8 hours)
    "story_mining": 100,  # Anecdote extraction and categorization (6-8 hours)
    # Very heavy research (150 credits ~ $300-375)
    "seo_keywords": 150,  # Comprehensive SEO keyword research (8-12 hours)
    "icp_workshop": 150,  # Ideal Customer Profile workshop (8-12 hours)
}

# Package pricing ($2/credit for standard packages)
STANDARD_PACKAGE_RATE = 2.0  # $2 per credit

# Additional credit pricing ($2.50/credit for top-ups)
ADDITIONAL_CREDIT_RATE = 2.5  # $2.50 per credit

# Minimum credits required for research tools
MIN_RESEARCH_TOOL_CREDITS = 50

# Maximum credits for a single operation
MAX_OPERATION_CREDITS = 200


def get_research_tool_cost(tool_name: str) -> int:
    """
    Get credit cost for a research tool.

    Args:
        tool_name: Research tool identifier

    Returns:
        Credit cost (0 if tool not found)
    """
    return RESEARCH_TOOL_COSTS.get(tool_name, 0)


def get_content_cost(content_type: str) -> int:
    """
    Get credit cost for content generation.

    Args:
        content_type: Content type identifier

    Returns:
        Credit cost (0 if content type not found)
    """
    return CONTENT_COSTS.get(content_type, 0)


def calculate_project_cost(
    num_blog_posts: int = 0,
    research_tools: list[str] | None = None,
) -> dict:
    """
    Calculate total credit cost for a project.

    Args:
        num_blog_posts: Number of blog posts to generate
        research_tools: List of research tool names

    Returns:
        Dictionary with cost breakdown
    """
    research_tools = research_tools or []

    # Blog post costs
    blog_cost = num_blog_posts * CONTENT_COSTS["blog_post"]

    # Research tool costs
    research_cost = 0
    research_breakdown = {}

    for tool_name in research_tools:
        cost = get_research_tool_cost(tool_name)
        if cost > 0:
            research_cost += cost
            research_breakdown[tool_name] = cost

    total_credits = blog_cost + research_cost

    return {
        "blog_posts": {"count": num_blog_posts, "credits_per_post": 20, "total": blog_cost},
        "research_tools": {"breakdown": research_breakdown, "total": research_cost},
        "total_credits": total_credits,
        "estimated_cost": {
            "standard_rate": total_credits * STANDARD_PACKAGE_RATE,
            "additional_rate": total_credits * ADDITIONAL_CREDIT_RATE,
        },
    }
