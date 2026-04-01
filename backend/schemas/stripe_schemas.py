"""Pydantic schemas for Stripe payment endpoints."""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class CheckoutSessionRequest(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str
    project_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentStatusResponse(BaseModel):
    session_id: str
    status: str  # pending | completed | failed | expired
    credits: Optional[int] = None
    project_id: Optional[str] = None
