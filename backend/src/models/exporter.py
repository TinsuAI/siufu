"""
Exporter database model for master data management
"""
from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class Exporter(Base):
    """Exporter model for master data of exporting companies"""

    __tablename__ = "exporters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, index=True
    )

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line3: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
        "Declaration", back_populates="exporter"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name_normalized", "country_code",
            name="uq_exporter_org_name_country"
        ),
        Index("idx_exporter_name_normalized", "name_normalized"),
        Index("idx_exporter_country_code", "country_code"),
        Index("idx_exporter_org_id", "organization_id"),
        Index("idx_exporter_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Exporter(id={self.id}, name={self.name}, country={self.country_code})>"
