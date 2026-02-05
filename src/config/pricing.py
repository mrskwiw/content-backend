"""
Centralized pricing configuration for the Content Jumpstart system.

This module provides:
- Global pricing constants ($40/post, $15 research add-on)
- Price calculation utilities
- Unlimited revision policy
"""
from typing import Dict
from pydantic import BaseModel


class PricingConfig(BaseModel):
    """Global pricing constants"""

    # Base pricing
    PRICE_PER_POST: float = 40.0
    RESEARCH_PRICE_PER_POST: float = 15.0  # Optional add-on per post

    # Minimum and maximum order sizes
    MIN_POSTS: int = 1
    MAX_POSTS: int = 100  # Soft limit for UI (can be overridden)

    # Revision policy
    UNLIMITED_REVISIONS: bool = True


def calculate_price(
    num_posts: int,
    research_per_post: bool = False,
    price_per_post: float = 40.0,
    research_price: float = 15.0
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


def calculate_price_from_quantities(
    template_quantities: Dict[int, int],
    research_per_post: bool = False,
    price_per_post: float = 40.0,
    research_price: float = 15.0
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
