"""
Knowledge Base Version database model
"""
from datetime import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, func, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class KnowledgeBaseType(str, enum.Enum):
    """Knowledge base type enumeration"""
    GOOD_LIST = "GOOD_LIST"
    TARIFF = "TARIFF"


class KnowledgeBaseStatus(str, enum.Enum):
    """Knowledge base status enumeration"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class KnowledgeBaseVersion(Base):
    """Knowledge base version model for tracking good list and tariff uploads"""

    __tablename__ = "knowledge_base_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[KnowledgeBaseType] = mapped_column(
        SQLEnum(KnowledgeBaseType), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[KnowledgeBaseStatus] = mapped_column(
        SQLEnum(KnowledgeBaseStatus),
        nullable=False,
        default=KnowledgeBaseStatus.ACTIVE
    )
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Unique constraint for organization, type, and version number
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "type", "version_number",
            name="uq_knowledge_base_version"
        ),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="knowledge_base_versions"
    )
    uploaded_by_user: Mapped["User"] = relationship(
        "User", back_populates="uploaded_knowledge_bases"
    )
    good_list_entries: Mapped[list["GoodListEntry"]] = relationship(
        "GoodListEntry", back_populates="version", cascade="all, delete-orphan"
    )
    tariff_rates: Mapped[list["TariffRate"]] = relationship(
        "TariffRate", back_populates="version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBaseVersion(id={self.id}, type={self.type}, version={self.version_number})>"
