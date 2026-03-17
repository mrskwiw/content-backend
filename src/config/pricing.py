"""
Centralized pricing configuration for the Content Jumpstart system.

This module provides:
- Global pricing constants ($40/post)
- Research tool catalog with a la carte pricing ($300-$600 per tool)
- Bundle discount definitions and auto-detection
- Price calculation utilities
- Unlimited revision policy

Note: Legacy per-post research add-on ($15/post) has been deprecated (Bug #43) in favor
      of the new research tools system which provides higher value and better pricing.
"""

from typing import Dict, List, TypedDict
from pydantic import BaseModel


class PricingConfig(BaseModel):
    """Global pricing constants"""

    # Base pricing
    PRICE_PER_POST: float = 40.0
    RESEARCH_PRICE_PER_POST: float = (
        0.0  # DEPRECATED (Bug #43): Topic research replaced by research tools ($300-$600 each)
    )

    # Minimum and maximum order sizes
    MIN_POSTS: int = 1
    MAX_POSTS: int = 100  # Soft limit for UI (can be overridden)

    # Revision policy
    UNLIMITED_REVISIONS: bool = True


def calculate_price(
    num_posts: int,
    research_per_post: bool = False,
    price_per_post: float = 40.0,
    research_price: float = 0.0,  # DEPRECATED (Bug #43): Set to 0.0, was 15.0
) -> float:
    """
    Calculate total price with optional research add-on.

    Args:
        num_posts: Number of posts to generate
        research_per_post: Whether to include research add-on
        price_per_post: Base price per post (default: $40)
        research_price: Research price per post (default: $15)

    Returns:
        Total price as float

    Examples:
        >>> calculate_price(30, research_per_post=False)
        1200.0
        >>> calculate_price(30, research_per_post=True)
        1650.0
        >>> calculate_price(50, research_per_post=True)
        2750.0
    """
    base = num_posts * price_per_post
    research = num_posts * research_price if research_per_post else 0.0
    return base + research


# ---------------------------------------------------------------------------
# Research Tool Catalog
# ---------------------------------------------------------------------------


class ToolDefinition(TypedDict):
    """Single research tool definition."""

    name: str
    price: float
    group: str


# All available research tools, keyed by tool ID.
TOOLS: Dict[str, ToolDefinition] = {
    "voice_analysis": {"name": "Voice Analysis", "price": 400.0, "group": "foundation"},
    "brand_archetype": {"name": "Brand Archetype", "price": 300.0, "group": "foundation"},
    "audience_research": {"name": "Audience Research", "price": 500.0, "group": "foundation"},
    "icp_workshop": {"name": "ICP Workshop", "price": 600.0, "group": "foundation"},
    "seo_keyword_research": {"name": "SEO Keyword Research", "price": 400.0, "group": "seo"},
    "competitive_analysis": {"name": "Competitive Analysis", "price": 500.0, "group": "seo"},
    "content_gap_analysis": {"name": "Content Gap Analysis", "price": 500.0, "group": "seo"},
    "content_audit": {"name": "Content Audit", "price": 400.0, "group": "advanced"},
    "platform_strategy": {"name": "Platform Strategy", "price": 300.0, "group": "advanced"},
    "content_calendar_strategy": {
        "name": "Content Calendar Strategy",
        "price": 300.0,
        "group": "advanced",
    },
    "story_mining_interview": {
        "name": "Story Mining Interview",
        "price": 500.0,
        "group": "advanced",
    },
    "market_trends": {"name": "Market Trends", "price": 400.0, "group": "advanced"},
}

# Known tool ID set for quick validation.
KNOWN_TOOL_IDS: frozenset = frozenset(TOOLS.keys())

# Tool IDs by group (used for bundle detection).
_FOUNDATION_TOOLS = frozenset(
    {"voice_analysis", "brand_archetype", "audience_research", "icp_workshop"}
)
_SEO_TOOLS = frozenset({"seo_keyword_research", "competitive_analysis", "content_gap_analysis"})
_ALL_STRATEGY_TOOLS = _FOUNDATION_TOOLS | _SEO_TOOLS  # 7 tools for Complete Strategy
_ALL_TOOLS = frozenset(TOOLS.keys())  # 12 tools for Ultimate Pack


class BundleDefinition(TypedDict):
    """Bundle definition with required tool IDs, bundle price, and name."""

    name: str
    required_tools: frozenset
    price: float
    ala_carte_price: float
    saves: float


# Ordered from most inclusive to least — detection logic must match this order.
BUNDLES: List[BundleDefinition] = [
    {
        "name": "Ultimate Pack",
        "required_tools": _ALL_TOOLS,
        "price": 4500.0,
        "ala_carte_price": 5100.0,
        "saves": 600.0,
    },
    {
        "name": "Complete Strategy",
        "required_tools": _ALL_STRATEGY_TOOLS,
        "price": 2400.0,
        "ala_carte_price": 3200.0,
        "saves": 800.0,
    },
    {
        "name": "Foundation Pack",
        "required_tools": _FOUNDATION_TOOLS,
        "price": 1500.0,
        "ala_carte_price": 1800.0,
        "saves": 300.0,
    },
    {
        "name": "SEO Pack",
        "required_tools": _SEO_TOOLS,
        "price": 1300.0,
        "ala_carte_price": 1400.0,
        "saves": 100.0,
    },
]


class ToolsCostResult(TypedDict):
    """Result of calculate_tools_cost()."""

    tools_cost: float
    discount_amount: float
    applied_bundles: List[str]


def calculate_tools_cost(selected_tools: List[str]) -> ToolsCostResult:
    """
    Calculate research tool cost with automatic bundle discount detection.

    Bundle detection priority (most inclusive wins for overlapping tool sets):
    1. All 12 tools selected → Ultimate Pack ($4,500)
    2. All 7 Foundation+SEO tools → Complete Strategy ($2,400)
    3. Otherwise: Foundation Pack if all 4 foundation tools present,
                  AND SEO Pack if all 3 SEO tools present (applied separately).
    4. Remaining advanced-group tools are always a la carte.

    Args:
        selected_tools: List of tool IDs from TOOLS catalog.

    Returns:
        Dict with tools_cost, discount_amount, and applied_bundles list.

    Examples:
        >>> calculate_tools_cost([])
        {'tools_cost': 0.0, 'discount_amount': 0.0, 'applied_bundles': []}
        >>> calculate_tools_cost(list(TOOLS.keys()))["tools_cost"]
        4500.0
    """
    if not selected_tools:
        return {"tools_cost": 0.0, "discount_amount": 0.0, "applied_bundles": []}

    selected_set = frozenset(selected_tools)
    ala_carte_total = sum(TOOLS[tid]["price"] for tid in selected_set if tid in TOOLS)

    applied_bundles: List[str] = []
    bundled_tools: frozenset = frozenset()
    bundle_price_total = 0.0

    # Step 1: Check mutually exclusive top-level bundles first.
    if _ALL_TOOLS.issubset(selected_set):
        # Ultimate Pack covers all 12 tools.
        bundle_price_total = 4500.0
        bundled_tools = _ALL_TOOLS
        applied_bundles.append("Ultimate Pack")
    elif _ALL_STRATEGY_TOOLS.issubset(selected_set):
        # Complete Strategy covers 7 Foundation + SEO tools.
        bundle_price_total = 2400.0
        bundled_tools = _ALL_STRATEGY_TOOLS
        applied_bundles.append("Complete Strategy")
    else:
        # Check Foundation Pack and SEO Pack independently.
        if _FOUNDATION_TOOLS.issubset(selected_set):
            bundle_price_total += 1500.0
            bundled_tools = bundled_tools | _FOUNDATION_TOOLS
            applied_bundles.append("Foundation Pack")
        if _SEO_TOOLS.issubset(selected_set):
            bundle_price_total += 1300.0
            bundled_tools = bundled_tools | _SEO_TOOLS
            applied_bundles.append("SEO Pack")

    # Step 2: Add a la carte price for any tools NOT covered by a bundle.
    unbundled_tools = selected_set - bundled_tools
    ala_carte_remainder = sum(TOOLS[tid]["price"] for tid in unbundled_tools if tid in TOOLS)

    tools_cost = bundle_price_total + ala_carte_remainder
    discount_amount = round(ala_carte_total - tools_cost, 2)

    return {
        "tools_cost": tools_cost,
        "discount_amount": discount_amount,
        "applied_bundles": applied_bundles,
    }


class FullPriceBreakdown(TypedDict):
    """Complete project price breakdown."""

    posts_cost: float
    research_addon_cost: float
    tools_cost: float
    discount_amount: float
    total_price: float
    applied_bundles: List[str]


def calculate_full_project_price(
    num_posts: int,
    research_per_post: bool = False,
    selected_tools: List[str] | None = None,
    price_per_post: float = 40.0,
    research_price: float = 0.0,  # DEPRECATED (Bug #43): Set to 0.0, was 15.0
) -> FullPriceBreakdown:
    """
    Calculate complete project price breakdown including posts, research add-on, and tools.

    Args:
        num_posts: Number of posts to generate.
        research_per_post: Whether to include per-post topic research add-on.
        selected_tools: List of tool IDs to include (None or [] means no tools).
        price_per_post: Base price per post (default: $40).
        research_price: Research add-on price per post (default: $15).

    Returns:
        Full breakdown with posts_cost, research_addon_cost, tools_cost,
        discount_amount, total_price, and applied_bundles.

    Examples:
        >>> calculate_full_project_price(30)["posts_cost"]
        1200.0
        >>> calculate_full_project_price(30, research_per_post=True)["research_addon_cost"]
        450.0
    """
    posts_cost = num_posts * price_per_post
    research_addon_cost = (num_posts * research_price) if research_per_post else 0.0
    tools_result = calculate_tools_cost(selected_tools or [])

    return {
        "posts_cost": posts_cost,
        "research_addon_cost": research_addon_cost,
        "tools_cost": tools_result["tools_cost"],
        "discount_amount": tools_result["discount_amount"],
        "total_price": posts_cost + research_addon_cost + tools_result["tools_cost"],
        "applied_bundles": tools_result["applied_bundles"],
    }


def calculate_price_from_quantities(
    template_quantities: Dict[int, int],
    research_per_post: bool = False,
    price_per_post: float = 40.0,
    research_price: float = 0.0,  # DEPRECATED (Bug #43): Set to 0.0, was 15.0
) -> float:
    """
    Calculate price from template quantities.

    Args:
        template_quantities: Dict mapping template_id -> quantity
        research_per_post: Whether to include research add-on
        price_per_post: Base price per post (default: $40)
        research_price: Research price per post (default: $15)

    Returns:
        Total price as float

    Example:
        >>> calculate_price_from_quantities({1: 3, 2: 5, 9: 2}, research_per_post=False)
        400.0  # 10 posts * $40
    """
    total_posts = sum(template_quantities.values())
    return calculate_price(total_posts, research_per_post, price_per_post, research_price)
