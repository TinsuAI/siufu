"""
Correction database model
"""
from datetime import datetime
import enum
import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.models.base import Base


class CorrectionType(str, enum.Enum):
    """Correction type enumeration"""
    TYPO = "TYPO"
    WRONG_EXTRACTION = "WRONG_EXTRACTION"
    WRONG_HS_CODE = "WRONG_HS_CODE"
    VALIDATION_FIX = "VALIDATION_FIX"
    OTHER = "OTHER"


class Correction(Base):
    """Correction model for tracking user corrections to AI extractions"""

    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    declaration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("declarations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)
    original_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    correction_type: Mapped[CorrectionType] = mapped_column(
        SQLEnum(CorrectionType), nullable=False
    )
    source_document: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Story 3.6 Expansion: New fields for inline flagging feature
    correction_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: AI Extraction Error, Wrong HS Code, Calculation Error, Missing Data, Format Issue, Other"
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Required user notes explaining why the correction is needed (max 500 chars)"
    )
    expected_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Required field: what the correct value should be (max 500 chars)"
    )
    screenshots: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Optional array of screenshot URLs showing where the correct data appears in the document (max 3)"
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    declaration: Mapped["Declaration"] = relationship(
        "Declaration", back_populates="corrections"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="corrections"
    )

    def __repr__(self) -> str:
        return f"<Correction(id={self.id}, field='{self.field_name}', type={self.correction_type})>"
