"""
Database model mixins for shared functionality.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to models.

    Soft delete marks records as deleted without removing them from the database.
    This enables:
    - GDPR Article 17 (Right to Erasure) compliance
    - CCPA Section 1798.105 (Right to Deletion) compliance
    - Audit trail preservation
    - Accidental deletion recovery
    - Analytics data retention (aggregated, anonymized)

    Usage:
        class MyModel(Base, SoftDeleteMixin):
            __tablename__ = "my_table"
            id = Column(String, primary_key=True)
            name = Column(String)

    Example:
        # Soft delete a record
        client = db.query(Client).filter(Client.id == client_id).first()
        client.soft_delete()
        db.commit()

        # Query active records only
        active_clients = db.query(Client).filter(Client.is_deleted.is_(False)).all()

        # Restore a soft-deleted record
        client.restore()
        db.commit()
    """

    # When was this record soft-deleted (NULL if active)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Is this record soft-deleted (for quick filtering)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def soft_delete(self):
        """
        Mark this record as deleted.

        Sets is_deleted=True and deleted_at=now().
        Does NOT commit the transaction - caller must commit.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """
        Restore a soft-deleted record.

        Sets is_deleted=False and deleted_at=None.
        Does NOT commit the transaction - caller must commit.
        """
        self.is_deleted = False
        self.deleted_at = None

    @property
    def is_active(self) -> bool:
        """Check if record is active (not deleted)."""
        return not self.is_deleted


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def get_active_query(session, model):
    """
    Helper function to get query filtered for active (non-deleted) records.

    Usage:
        active_clients = get_active_query(db, Client).all()
    """
    return session.query(model).filter(model.is_deleted.is_(False))
