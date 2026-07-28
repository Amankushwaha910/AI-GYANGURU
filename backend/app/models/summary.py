"""
Summary model — stores AI-generated topic summaries.
"""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Summary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "summaries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploads.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # Which sections were requested
    sections_requested: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Structured content — each key is a section name
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Metadata
    is_from_file: Mapped[bool] = mapped_column(default=False, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    upload: Mapped[Optional["Upload"]] = relationship("Upload")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_summaries_user_topic", "user_id", "topic"),
        Index("ix_summaries_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Summary id={self.id} topic={self.topic[:50]}>"
