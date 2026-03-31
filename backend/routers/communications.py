"""Communications API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.auth_dependency import get_current_user
from backend.models import User, Communication
from backend.services import crud

router = APIRouter()


class CommunicationCreate(BaseModel):
    """Input for creating a communication"""

    client_id: int
    type: str  # email, call, meeting, note
    subject: str
    content: str = ""
    direction: str = "outbound"  # inbound, outbound
    duration: str = ""  # For calls


class CommunicationResponse(BaseModel):
    """Communication response"""

    id: int
    client_id: int
    user_id: int
    type: str
    subject: str
    content: str
    direction: str
    duration: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/clients/{client_id}/communications", response_model=List[CommunicationResponse])
def get_client_communications(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all communications for a client"""
    # Verify client exists and user has access
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if client.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Get communications ordered by date (newest first)
    communications = (
        db.query(Communication)
        .filter(Communication.client_id == client_id)
        .order_by(Communication.created_at.desc())
        .all()
    )

    return communications


@router.post("/communications", response_model=CommunicationResponse, status_code=201)
def create_communication(
    input: CommunicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new communication record"""
    # Verify client exists and user has access
    client = crud.get_client(db, input.client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if client.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Create communication
    communication = Communication(
        client_id=input.client_id,
        user_id=current_user.id,
        type=input.type,
        subject=input.subject,
        content=input.content,
        direction=input.direction,
        duration=input.duration,
    )

    db.add(communication)
    db.commit()
    db.refresh(communication)

    return communication


@router.delete("/communications/{communication_id}", status_code=204)
def delete_communication(
    communication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a communication"""
    communication = db.query(Communication).filter(Communication.id == communication_id).first()

    if not communication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication not found")

    # Verify user created this communication or is superuser
    if communication.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(communication)
    db.commit()

    return None
