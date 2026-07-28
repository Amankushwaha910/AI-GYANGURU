"""
Analytics event model — immutable audit log of all learning activities.
"""
import uuid
from enum import Enum

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class EventType(str, Enum):
    summary_generated = "summary_generated"
    explanation_generated = "explanation_generated"
    quiz_generated = "quiz_generated"
    quiz_completed = "quiz_completed"
    file_uploaded = "file_uploaded"
    topic_studied = "topic_studied"


class AnalyticsEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analytics_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(String(50), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional references to the generated resource
    resource_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_analytics_user_created", "user_id", "created_at"),
        Index("ix_analytics_user_event", "user_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsEvent type={self.event_type} topic={self.topic[:30]}>"
