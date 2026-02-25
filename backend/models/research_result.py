"""
Research Result Model

Stores results from research tools (voice analysis, SEO, competitive analysis, etc.)
for persistence and inclusion in deliverables.

TR-021: User must own the parent project/client to access research results.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database import Base


class ResearchResult(Base):
    """
    Research result from tool execution.

    Relationships:
    - user: User who executed the research
    - client: Client associated with the research
    - project: Project associated with the research (optional)
    """

    __tablename__ = "research_results"

    # Primary key
    id = Column(String, primary_key=True)  # "res-{uuid}"

    # Foreign keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    # Tool information
    tool_name = Column(String, nullable=False, index=True)
    tool_label = Column(String)
    tool_price = Column(Float)

    # Data (JSON for flexibility across different tools)
    params = Column(JSON)  # Input parameters
    outputs = Column(JSON)  # File paths or content
    data = Column(JSON)  # Structured results

    # Execution status
    status = Column(String, default="completed", index=True)
    error_message = Column(Text)
    duration_seconds = Column(Float)

    # Caching
    cache_key = Column(String, index=True)
    is_cached_result = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("backend.models.user.User", foreign_keys=[user_id])
    client = relationship("backend.models.client.Client", foreign_keys=[client_id])
    project = relationship("backend.models.project.Project", foreign_keys=[project_id])

    def __repr__(self):
        return f"<ResearchResult(id={self.id}, tool={self.tool_name}, status={self.status})>"
