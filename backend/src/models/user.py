"""
User database model
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    processor = "processor"
    admin = "admin"


class User(Base):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.processor
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )
    created_declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration",
        foreign_keys="Declaration.created_by_user_id",
        back_populates="created_by_user"
    )
    approved_declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration",
        foreign_keys="Declaration.approved_by_user_id",
        back_populates="approved_by_user"
    )
    corrections: Mapped[list["Correction"]] = relationship(
        "Correction", back_populates="user"
    )
    uploaded_knowledge_bases: Mapped[list["KnowledgeBaseVersion"]] = relationship(
        "KnowledgeBaseVersion", back_populates="uploaded_by_user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"
