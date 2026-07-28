"""
History item model — unified view of all user-generated content.
"""
import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class HistoryItemType(str, Enum):
    summary = "summary"
    explanation = "explanation"
    quiz = "quiz"
    upload = "upload"


class HistoryItem(Base, UUIDMixin, TimestampMixin):
    """
    Denormalized history log. Each row points to a resource via resource_id.
    Allows efficient paginated history browsing without joining multiple tables.
    """
    __tablename__ = "history_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[HistoryItemType] = mapped_column(
        String(20), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    resource_id: Mapped[str] = mapped_column(
        String(36), nullable=False  # UUID of the linked resource
    )

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_history_user_type_created", "user_id", "item_type", "created_at"),
        Index("ix_history_user_topic", "user_id", "topic"),
    )

    def __repr__(self) -> str:
        return f"<HistoryItem type={self.item_type} topic={self.topic[:30]}>"
