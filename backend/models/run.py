"""
Run model for generation executions.
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class Run(Base):
    """Generation execution run"""

    __tablename__ = "runs"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    is_batch = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(
        String, nullable=False, default="pending"
    )  # pending, running, succeeded, failed
    logs = Column(JSON)  # Array of log messages
    error_message = Column(String)  # Error details if failed

    # Token usage tracking (cumulative for all posts in this run)
    total_input_tokens = Column(Integer, nullable=True)
    total_output_tokens = Column(Integer, nullable=True)
    total_cache_creation_tokens = Column(Integer, nullable=True)
    total_cache_read_tokens = Column(Integer, nullable=True)
    total_cost_usd = Column(Float, nullable=True)  # Actual cost after completion
    estimated_cost_usd = Column(Float, nullable=True)  # Estimated cost before/during execution

    # Relationships (using fully qualified paths to avoid conflicts with Pydantic models in src.models)
    project = relationship("backend.models.project.Project", back_populates="runs")
    posts = relationship(
        "backend.models.post.Post", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Run {self.id} ({self.status})>"
