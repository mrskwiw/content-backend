"""
Pydantic schemas for Project API.
"""

from typing import Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from backend.utils.input_validators import (
    validate_string_field,
    validate_id_field,
)


class ProjectBase(BaseModel):
    """Base project schema"""

    name: str
    client_id: str = Field(validation_alias=AliasChoices("clientId", "client_id"))

    # Template selection (NEW: template_quantities replaces templates)
    templates: Optional[List[str]] = None  # DEPRECATED: Legacy support, use template_quantities
    template_quantities: Optional[Dict[str, int]] = Field(
        default=None,
        validation_alias=AliasChoices("templateQuantities", "template_quantities"),
        description="Dict mapping template_id (str) to quantity (int)",
    )
    num_posts: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("numPosts", "num_posts"),
        description="Total post count (auto-calculated from template_quantities)",
    )

    # Pricing (NEW: flexible per-post pricing)
    price_per_post: Optional[float] = Field(
        default=40.0,
        validation_alias=AliasChoices("pricePerPost", "price_per_post"),
        description="Base price per post",
    )
    research_price_per_post: Optional[float] = Field(
        default=0.0,
        validation_alias=AliasChoices("researchPricePerPost", "research_price_per_post"),
        description="Research add-on per post",
    )
    total_price: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("totalPrice", "total_price"),
        description="Total project price (auto-calculated)",
    )

    # Configuration
    platforms: Optional[List[str]] = None
    tone: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both snake_case and camelCase for validation
    )

    # TR-003: Input validation
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name (prevent XSS, SQL injection)"""
        return validate_string_field(v, field_name="name", min_length=3, max_length=200)

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client ID format"""
        return validate_id_field(
            v, field_name="client_id", prefix="client-", min_length=8, max_length=50
        )

    @field_validator("num_posts")
    @classmethod
    def validate_num_posts(cls, v: Optional[int]) -> Optional[int]:
        """Validate post count is within reasonable bounds"""

        # Tone is free-form text to allow brand-specific descriptions
        # Examples: professional, casual, friendly, innovative, technical, empathetic,
        #          authoritative, educational, motivational, analytical, inspirational, etc.
        return validate_string_field(
            v, field_name="tone", min_length=3, max_length=100, allow_empty=False
        )

    @field_validator("template_quantities")
    @classmethod
    def validate_template_quantities(cls, v: Optional[Dict[str, int]]) -> Optional[Dict[str, int]]:
        """Validate template quantities dict"""
