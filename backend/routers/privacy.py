"""
Privacy API Router - GDPR/CCPA Compliance Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services import data_privacy_service
from backend.middleware.auth_dependency import get_current_user

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: str,
    cascade: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        result = data_privacy_service.soft_delete_client(client_id, db, cascade)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/clients/{client_id}/anonymize")
def anonymize_client(
    client_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        result = data_privacy_service.anonymize_client(client_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/clients/{client_id}/export")
def export_client(
    client_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        result = data_privacy_service.export_client_data(client_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/clients/{client_id}/restore")
def restore_client(
    client_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        result = data_privacy_service.restore_soft_deleted_client(client_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
