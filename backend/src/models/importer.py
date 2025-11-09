"""
Importer database model for master data management
"""
from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class Importer(Base):
    """Importer model for master data of importing companies"""

    __tablename__ = "importers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core identification
    tax_code: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # Contact info
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    first_seen_declaration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    last_seen_declaration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    declaration_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Quality tracking
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    last_reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    last_reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[last_reviewed_by_user_id]
    )
    declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration", back_populates="importer"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "tax_code", "deleted_at",
            name="uq_importer_org_tax_code"
        ),
        Index("idx_importer_tax_code", "tax_code"),
        Index("idx_importer_name_normalized", "name_normalized"),
        Index("idx_importer_org_id", "organization_id"),
        Index("idx_importer_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Importer(id={self.id}, tax_code={self.tax_code}, name={self.name})>"
