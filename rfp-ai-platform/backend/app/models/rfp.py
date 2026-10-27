import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Uuid, ForeignKey, Text, Enum as SQLEnum, Boolean
import enum
from app.models.base import Base

class RFPStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"

class RequirementPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RequirementStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"

class RFPProject(Base):
    __tablename__ = "rfp_projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RFPStatus] = mapped_column(SQLEnum(RFPStatus), default=RFPStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="rfp_projects")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="rfp_project")
    requirements: Mapped[list["Requirement"]] = relationship("Requirement", back_populates="rfp_project")

class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rfp_project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rfp_projects.id"))
    requirement_id: Mapped[str] = mapped_column(String(100)) # E.g., "REQ-001"
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    priority: Mapped[RequirementPriority] = mapped_column(SQLEnum(RequirementPriority), default=RequirementPriority.MEDIUM)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deliverable: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RequirementStatus] = mapped_column(SQLEnum(RequirementStatus), default=RequirementStatus.PENDING)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(nullable=True)
    source_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    rfp_project: Mapped["RFPProject"] = relationship("RFPProject", back_populates="requirements")
    responses: Mapped[list["Response"]] = relationship("Response", back_populates="requirement")
