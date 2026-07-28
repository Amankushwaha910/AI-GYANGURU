"""
AI request/response logging models.
Every AI call is logged for audit, debugging, and token usage tracking.
"""
import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AIRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # summary/explanation/quiz
    prompt_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True  # SHA-256 for deduplication
    )
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    response: Mapped[Optional["AIResponse"]] = relationship(
        "AIResponse", back_populates="request", uselist=False, cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_ai_requests_user_created", "user_id", "created_at"),
    )


class AIResponse(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_responses"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finish_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_valid_json: Mapped[bool] = mapped_column(default=False, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    request: Mapped["AIRequest"] = relationship("AIRequest", back_populates="response")
