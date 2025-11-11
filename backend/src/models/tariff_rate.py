"""
Tariff Rate database model
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class TariffRate(Base):
    """Tariff rate model for HS code tax rates"""

    __tablename__ = "tariff_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hs_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    import_duty_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    trade_agreement: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_base_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
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
        "Organization", back_populates="tariff_rates"
    )
    version: Mapped["KnowledgeBaseVersion"] = relationship(
        "KnowledgeBaseVersion", back_populates="tariff_rates"
    )

    def __repr__(self) -> str:
        return f"<TariffRate(id={self.id}, hs_code='{self.hs_code}')>"
