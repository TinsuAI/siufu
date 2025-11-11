"""
Good List Entry database model
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class GoodListEntry(Base):
    """Good list entry model for product history"""

    __tablename__ = "good_list_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    hs_code: Mapped[str] = mapped_column(String(8), nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_base_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="good_list_entries"
    )
    version: Mapped["KnowledgeBaseVersion"] = relationship(
        "KnowledgeBaseVersion", back_populates="good_list_entries"
    )

    def __repr__(self) -> str:
        return f"<GoodListEntry(id={self.id}, hs_code='{self.hs_code}')>"
