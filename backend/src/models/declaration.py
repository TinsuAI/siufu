"""
Declaration database model
"""
from datetime import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.models.base import Base


class DeclarationStatus(str, enum.Enum):
    """Declaration status enumeration"""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class Declaration(Base):
    """Declaration model for customs declarations"""

    __tablename__ = "declarations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[DeclarationStatus] = mapped_column(
        SQLEnum(DeclarationStatus),
        nullable=False,
        default=DeclarationStatus.UPLOADED,
        index=True
    )
    uploaded_files: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    draft_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    validation_warnings: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    confidence_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    processing_progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="declarations"
    )
    created_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_declarations"
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
        back_populates="approved_declarations"
    )
    corrections: Mapped[list["Correction"]] = relationship(
        "Correction", back_populates="declaration", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Declaration(id={self.id}, status={self.status})>"
