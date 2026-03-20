"""
Pydantic schemas for Brief API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, AliasChoices, field_serializer


class BriefCreate(BaseModel):
    """
    Schema for creating a brief from pasted text.

    TR-022: Mass assignment protection
    - Only allows: project_id, content
    - Protected fields set by system: id, source, file_path, created_at
    """

    project_id: str = Field(..., validation_alias=AliasChoices("project_id", "projectId"))
    content: str = Field(..., validation_alias=AliasChoices("content"))

    model_config = ConfigDict(
        populate_by_name=True, extra="forbid"  # TR-022: Reject unknown fields
    )


class BriefUpdate(BaseModel):
    """
    Schema for updating a brief.

    TR-022: Mass assignment protection
    - Only allows: content
    - Protected fields (never updatable): id, project_id, source, file_path, created_at
    """

    content: Optional[str] = Field(default=None, validation_alias=AliasChoices("content"))

    model_config = ConfigDict(
        populate_by_name=True, extra="forbid"  # TR-022: Reject unknown fields
    )


class BriefResponse(BaseModel):
    """
    Schema for brief response.

    TR-022: Includes all fields including read-only ones
    """

    id: str
    project_id: str = Field(..., serialization_alias="projectId")
    content: str
    source: str  # "upload" or "paste"
    file_path: Optional[str] = Field(default=None, serialization_alias="filePath")
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both snake_case and camelCase
    )

    @field_serializer("created_at")
    def serialize_datetime(self, value, _info):
        """Serialize datetime with UTC timezone."""
        if value is None:
            return None
        from datetime import timezone

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
