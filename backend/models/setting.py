"""Settings model for storing user preferences and integration configurations"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class Setting(Base):
    """
    User settings and integration configurations.

    Supports storing encrypted API keys and preferences.
    Each user has their own settings.
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Setting identification
    key = Column(
        String(100), nullable=False, index=True
    )  # e.g., "web_search_provider", "brave_api_key"
    value = Column(Text, nullable=True)  # Encrypted for sensitive values

    # Metadata
    category = Column(String(50), nullable=False, index=True)  # e.g., "integrations", "preferences"
    is_encrypted = Column(Integer, default=0)  # 1 if value is encrypted, 0 if plain text

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<Setting(id={self.id}, user_id={self.user_id}, key='{self.key}', category='{self.category}')>"
