"""
Pydantic schemas for credit system API.

Request and response models for:
- Credit transactions
- Credit packages
- Credit purchases
- Credit balance
- Cost estimation
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# Credit Transaction Schemas
class CreditTransactionBase(BaseModel):
    """Base credit transaction schema."""

    amount: int
    transaction_type: str = Field(..., pattern="^(purchase|deduction|refund|admin_adjustment)$")
    description: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class CreditTransactionCreate(CreditTransactionBase):
    """Schema for creating a credit transaction."""

    user_id: str


class CreditTransactionResponse(CreditTransactionBase):
    """Schema for credit transaction response."""

    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Credit Package Schemas
class CreditPackageBase(BaseModel):
    """Base credit package schema."""

    name: str
    credits: int = Field(..., gt=0)
    price_usd: float = Field(..., gt=0)
    package_type: str = Field(..., pattern="^(package|additional)$")
    description: Optional[str] = None


class CreditPackageResponse(CreditPackageBase):
    """Schema for credit package response."""

    id: str
    is_active: bool
    rate_per_credit: float

    class Config:
        from_attributes = True

    @field_validator("rate_per_credit", mode="before")
    @classmethod
    def calculate_rate(cls, v, info):
        """Calculate rate per credit from price and credits."""
        # If rate_per_credit is already set, use it
        if v is not None:
            return v

        # Otherwise calculate from price_usd and credits
        data = info.data
        if "price_usd" in data and "credits" in data:
            return data["price_usd"] / data["credits"]

        return 0


# Credit Purchase Schemas
class CreditPurchaseRequest(BaseModel):
    """Request schema for purchasing credits."""

    package_id: str
    payment_reference: Optional[str] = None


class CreditPurchaseResponse(BaseModel):
    """Response schema for credit purchase."""

    transaction: CreditTransactionResponse
    new_balance: int
    package_info: CreditPackageResponse


# Credit Balance Schemas
class CreditBalanceResponse(BaseModel):
    """Response schema for credit balance."""

    balance: int
    total_purchased: int
    total_used: int
    is_enterprise: bool
    custom_credit_rate: Optional[float] = None


# Credit Summary Schemas
class TransactionSummary(BaseModel):
    """Summary of a transaction for credit summary."""

    id: str
    amount: int
    type: str
    description: str
    created_at: Optional[str] = None


class PackageSummary(BaseModel):
    """Summary of a package for credit summary."""

    id: str
    name: str
    credits: int
    price_usd: float
    rate_per_credit: float
    description: Optional[str] = None


class CreditSummaryResponse(BaseModel):
    """Comprehensive credit summary response."""

    balance: int
    total_purchased: int
    total_used: int
    is_enterprise: bool
    custom_credit_rate: Optional[float] = None
    enterprise_notes: Optional[str] = None
    total_transactions: int
    recent_transactions: List[TransactionSummary]
    available_packages: dict  # {standard: [...], additional: [...]}


# Cost Estimation Schemas
class CostEstimationRequest(BaseModel):
    """Request schema for cost estimation."""

    num_posts: int = Field(default=0, ge=0)
    research_tools: Optional[List[str]] = None


class PostCostBreakdown(BaseModel):
    """Post cost breakdown."""

    count: int
    credits_each: int
    total_credits: int


class ResearchToolCost(BaseModel):
    """Research tool cost breakdown."""

    tool: str
    credits: int


class ResearchCostBreakdown(BaseModel):
    """Research cost breakdown."""

    tools: List[ResearchToolCost]
    total_credits: int


class CostEstimateResponse(BaseModel):
    """Response schema for cost estimation."""

    posts: PostCostBreakdown
    research_tools: ResearchCostBreakdown
    total_credits: int
    estimated_cost_usd: dict  # {standard_package: float, additional_credits: float}


# Admin Adjustment Schemas
class AdminCreditAdjustmentRequest(BaseModel):
    """Request schema for admin credit adjustment."""

    user_id: str
    amount: int = Field(..., description="Positive to add, negative to remove")
    description: str


class AdminCreditAdjustmentResponse(BaseModel):
    """Response schema for admin credit adjustment."""

    transaction: CreditTransactionResponse
    new_balance: int


# Transaction Filter Schemas
class TransactionFilterParams(BaseModel):
    """Query parameters for filtering transactions."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    transaction_type: Optional[str] = Field(
        default=None, pattern="^(purchase|deduction|refund|admin_adjustment)$"
    )
