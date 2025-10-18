"""
Organization database model
"""
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class Organization(Base):
    """Organization model for multi-tenant architecture"""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration", back_populates="organization", cascade="all, delete-orphan"
    )
    knowledge_base_versions: Mapped[list["KnowledgeBaseVersion"]] = relationship(
        "KnowledgeBaseVersion", back_populates="organization", cascade="all, delete-orphan"
    )
    good_list_entries: Mapped[list["GoodListEntry"]] = relationship(
        "GoodListEntry", back_populates="organization", cascade="all, delete-orphan"
    )
    tariff_rates: Mapped[list["TariffRate"]] = relationship(
        "TariffRate", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}')>"
