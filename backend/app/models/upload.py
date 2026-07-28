"""
Upload model — tracks every file uploaded by a user.
"""
import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UploadStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Upload(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "uploads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, etc.
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[UploadStatus] = mapped_column(
        String(20), nullable=False, default=UploadStatus.pending
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_used: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_uploads_user_id_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Upload id={self.id} file={self.original_filename} status={self.status}>"
