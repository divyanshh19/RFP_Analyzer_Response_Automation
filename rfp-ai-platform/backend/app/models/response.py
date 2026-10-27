import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Uuid, ForeignKey, Text, Enum as SQLEnum, Float, Integer
import enum
from app.models.base import Base

class ResponseStatus(str, enum.Enum):
    AI_GENERATED = "AI_GENERATED"
    EDITED = "EDITED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requirements.id"))
    ai_response: Mapped[str] = mapped_column(Text)
    final_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ResponseStatus] = mapped_column(SQLEnum(ResponseStatus), default=ResponseStatus.AI_GENERATED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="responses")
    sources: Mapped[list["Source"]] = relationship("Source", back_populates="response")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="response")

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responses.id"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    chunk_id: Mapped[str] = mapped_column(String(100))
    page_number: Mapped[int] = mapped_column(Integer)
    section_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    response: Mapped["Response"] = relationship("Response", back_populates="sources")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responses.id"))
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50)) # e.g. APPROVED, REJECTED, EDITED
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    response: Mapped["Response"] = relationship("Response", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews")
