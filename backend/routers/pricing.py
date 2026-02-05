"""
Pricing API endpoints.

Provides pricing configuration and price calculations
for the operator dashboard and external integrations.
"""

import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Query, HTTPException, Request, status, Body
from pydantic import BaseModel

# Add project root to path to import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.pricing import (  # noqa: E402
    calculate_price,
    calculate_price_from_quantities,
    PricingConfig,
)
from backend.utils.http_rate_limiter import lenient_limiter  # noqa: E402


router = APIRouter()


class PricingConfigResponse(BaseModel):
    """Response model for pricing configuration"""

    pricePerPost: float
    researchPricePerPost: float
    minPosts: int
    maxPosts: int
    unlimitedRevisions: bool


class CalculatePriceResponse(BaseModel):
    """Response model for price calculation"""

    numPosts: int
    researchIncluded: bool
    pricePerPost: float
    researchPricePerPost: float
    totalPrice: float


@router.get("/config", response_model=PricingConfigResponse)
@lenient_limiter.limit("1000/hour")  # TR-004: Cheap read operation
async def get_pricing_config(request: Request) -> PricingConfigResponse:
    """
    Get current pricing configuration.

    Rate limit: 1000/hour (cheap read operation)

    Returns global pricing constants like price per post,
    research pricing, and revision policy.

    Example response:
    ```json
    {
        "pricePerPost": 40.0,
        "researchPricePerPost": 15.0,
        "minPosts": 1,
        "maxPosts": 100,
        "unlimitedRevisions": true
    }
    ```
    """
    config = PricingConfig()
    return PricingConfigResponse(
        pricePerPost=config.PRICE_PER_POST,
        researchPricePerPost=config.RESEARCH_PRICE_PER_POST,
        minPosts=config.MIN_POSTS,
        maxPosts=config.MAX_POSTS,
        unlimitedRevisions=config.UNLIMITED_REVISIONS,
    )


@router.get("/calculate", response_model=CalculatePriceResponse)
@router.post("/calculate", response_model=CalculatePriceResponse)
@lenient_limiter.limit("1000/hour")  # TR-004: Cheap operation (calculation only)
async def calculate_custom_price(
    request: Request,
    num_posts: int = Query(None, ge=1, description="Number of posts to generate"),
    research: bool = Query(False, description="Include research add-on"),
    body: Optional[dict] = Body(None),
) -> CalculatePriceResponse:
    """
    Calculate price for custom configuration.

    Rate limit: 1000/hour (cheap calculation operation)

    Supports both GET (query params) and POST (JSON body):
    - GET: /api/pricing/calculate?num_posts=30&research=true
    - POST: /api/pricing/calculate with {"template_quantities": {"1": 5}}

    Args:
        num_posts: Number of posts (must be >= 1) - for GET requests
        research: Whether to include research add-on - for GET requests
        body: JSON body for POST requests with template_quantities

    Returns:
        Price calculation breakdown

    Example response:
    ```json
    {
        "numPosts": 30,
        "researchIncluded": true,
        "pricePerPost": 40.0,
        "researchPricePerPost": 15.0,
        "totalPrice": 1650.0
    }
    ```
    """
    config = PricingConfig()

    # Handle POST with template_quantities
    if body and "template_quantities" in body:
        # Calculate total posts from template quantities
        template_quantities: Dict[str, int] = body["template_quantities"]
        calculated_num_posts = sum(template_quantities.values())
        research_requested = body.get("research", False)

        price = calculate_price(
            num_posts=calculated_num_posts,
            research_per_post=research_requested,
            price_per_post=config.PRICE_PER_POST,
            research_price=config.RESEARCH_PRICE_PER_POST,
        )

        return CalculatePriceResponse(
            numPosts=calculated_num_posts,
            researchIncluded=research_requested,
            pricePerPost=config.PRICE_PER_POST,
            researchPricePerPost=config.RESEARCH_PRICE_PER_POST if research_requested else 0.0,
            totalPrice=price,
        )

    # Handle GET with query params
    if num_posts is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_posts query parameter is required for GET requests",
        )

    price = calculate_price(
        num_posts=num_posts,
        research_per_post=research,
        price_per_post=config.PRICE_PER_POST,
        research_price=config.RESEARCH_PRICE_PER_POST,
    )

    return CalculatePriceResponse(
        numPosts=num_posts,
        researchIncluded=research,
        pricePerPost=config.PRICE_PER_POST,
        researchPricePerPost=config.RESEARCH_PRICE_PER_POST if research else 0.0,
        totalPrice=price,
    )


@router.post("/calculate-from-quantities", response_model=CalculatePriceResponse)
@lenient_limiter.limit("1000/hour")  # TR-004: Cheap operation (calculation only)
async def calculate_price_from_template_quantities(
    request: Request,
    template_quantities: Dict[str, int],
    research: bool = False,
) -> CalculatePriceResponse:
    """
    Calculate price from template quantities.

    Rate limit: 1000/hour (cheap calculation operation)

    Useful for custom template selections where the user specifies
    exact quantities for each template.

    Args:
        template_quantities: Dict mapping template_id (as string) -> quantity
        research: Whether to include research add-on

    Returns:
        Price calculation breakdown

    Example request body:
    ```json
    {
        "template_quantities": {"1": 3, "2": 5, "9": 2},
        "research": false
    }
    ```

    Example response:
    ```json
    {
        "numPosts": 10,
        "researchIncluded": false,
        "pricePerPost": 40.0,
        "researchPricePerPost": 0.0,
        "totalPrice": 400.0
    }
    ```
    """
    # Convert string keys to integers
    quantities_int = {int(k): v for k, v in template_quantities.items()}

    config = PricingConfig()
    price = calculate_price_from_quantities(
        template_quantities=quantities_int,
        research_per_post=research,
        price_per_post=config.PRICE_PER_POST,
        research_price=config.RESEARCH_PRICE_PER_POST,
    )

    total_posts = sum(quantities_int.values())

    return CalculatePriceResponse(
        numPosts=total_posts,
        researchIncluded=research,
        pricePerPost=config.PRICE_PER_POST,
        researchPricePerPost=config.RESEARCH_PRICE_PER_POST if research else 0.0,
        totalPrice=price,
    )
