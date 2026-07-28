"""
File upload schemas.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.upload import UploadStatus


class UploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    status: UploadStatus
    ocr_used: bool
    has_extracted_text: bool
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadListItem(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    status: UploadStatus
    created_at: datetime

    model_config = {"from_attributes": True}
