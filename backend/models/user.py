"""
User model for authentication.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base
from backend.models.mixins import SoftDeleteMixin
from backend.config import settings


class User(Base, SoftDeleteMixin):
    """User account for operator authentication"""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Credit system fields
    credit_balance = Column(
        Integer, default=100000 if settings.DEBUG_MODE else 1000, nullable=False
    )  # 100k credits in debug/test, 1000 in production
    total_credits_purchased = Column(Integer, default=0, nullable=False)
    total_credits_used = Column(Integer, default=0, nullable=False)

    # Enterprise custom pricing
    is_enterprise = Column(Boolean, default=False, nullable=False)
    custom_credit_rate = Column(Float, nullable=True)  # Custom $/credit rate (e.g., 1.50)
    enterprise_notes = Column(Text, nullable=True)  # Admin notes about enterprise agreement
    # MFA (Two-Factor Authentication) - TR-008
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String, nullable=True)  # TOTP secret (encrypted)
    mfa_backup_codes = Column(Text, nullable=True)  # JSON array of hashed backup codes
    mfa_enforced = Column(Boolean, default=False, nullable=False)  # Admin enforcement flag

    # Relationships
    settings = relationship("Setting", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
