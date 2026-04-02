"""Communications API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.auth_dependency import get_current_user
from backend.models import User, Communication
from backend.services import crud
from agent.email_system import EmailSystem, EmailMessage, EmailType as AgentEmailType

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


class SendEmailInput(BaseModel):
    """Input for sending an email to a client"""

    email_type: str = (
        "general"  # general, deliverable, feedback_request, invoice_reminder, revision_confirmation
    )
    subject: str
    content: str  # Full pre-rendered email body from the frontend


class SendEmailResponse(BaseModel):
    """Response after sending an email to a client"""

    success: bool
    status: str  # sent | logged | failed
    detail: str
    communication_id: int


@router.post("/clients/{client_id}/send-email", response_model=SendEmailResponse)
def send_client_email(
    client_id: int,
    input: SendEmailInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send an email to a client and record it in the communication log.

    In production (SMTP configured): delivers via SMTP.
    In development (no SMTP): writes to data/email_logs/ and marks status as 'logged'.
    Either way, a Communication record is created for the audit trail.
    """
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if client.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not client.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client has no email address on file",
        )

    # Map UI email_type to the agent's EmailType enum (fallback to GENERAL)
    try:
        agent_email_type = AgentEmailType(input.email_type)
    except ValueError:
        agent_email_type = AgentEmailType.GENERAL

    # Build the message from the pre-rendered subject + body
    from datetime import datetime

    email_system = EmailSystem()
    message = EmailMessage(
        message_id=f"email_{int(datetime.utcnow().timestamp())}",
        to_email=client.email,
        subject=input.subject,
        body_text=input.content,
        email_type=agent_email_type,
    )

    success, send_detail = email_system.send_email(message)

    # Always log the communication regardless of send outcome
    communication = Communication(
        client_id=client_id,
        user_id=current_user.id,
        type="email",
        subject=input.subject,
        content=input.content,
        direction="outbound",
        duration="",
    )
    db.add(communication)
    db.commit()
    db.refresh(communication)

    return SendEmailResponse(
        success=success,
        status=message.status,
        detail=send_detail or ("Email sent successfully" if success else "Failed to send email"),
        communication_id=communication.id,
    )


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
