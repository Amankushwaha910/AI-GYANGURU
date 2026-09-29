"""
File upload routes — /api/v1/files
"""
import math
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, CurrentUserFast
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.upload import UploadListItem, UploadResponse
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["File Upload"])


@router.post("", response_model=APIResponse[UploadResponse], status_code=201)
async def upload_file(
    current_user: CurrentUserFast,
    background_tasks: BackgroundTasks,   # injected by FastAPI — NOT a default value
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file (PDF, DOCX, TXT, or image).
    Text extraction runs as a background task after the 201 response is sent.
    Poll GET /files/{id} to check when status becomes 'completed'.
    """
    service = FileService(db)
    upload = await service.upload_and_process(
        user_id=current_user.id,
        file=file,
        background_tasks=background_tasks,
    )
    return APIResponse(
        data=UploadResponse(
            id=upload.id,
            original_filename=upload.original_filename,
            file_type=upload.file_type,
            file_size_bytes=upload.file_size_bytes,
            status=upload.status,
            ocr_used=upload.ocr_used,
            has_extracted_text=bool(upload.extracted_text),
            error_message=upload.error_message,
            created_at=upload.created_at,
        ),
        message="File uploaded. Text extraction in progress.",
    )


@router.get("", response_model=PaginatedResponse[UploadListItem])
async def list_files(
    current_user: CurrentUserFast,   # fast — no profile needed for file list
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    """List the current user's uploaded files."""
    service = FileService(db)
    uploads, total = await service.list_uploads(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        data=[UploadListItem.model_validate(u) for u in uploads],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/{upload_id}", response_model=APIResponse[UploadResponse])
async def get_file(
    upload_id: UUID,
    current_user: CurrentUserFast,   # fast — polled every 3 s, profile not needed
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific uploaded file including processing status."""
    service = FileService(db)
    upload = await service.get_upload(current_user.id, upload_id)
    return APIResponse(
        data=UploadResponse(
            id=upload.id,
            original_filename=upload.original_filename,
            file_type=upload.file_type,
            file_size_bytes=upload.file_size_bytes,
            status=upload.status,
            ocr_used=upload.ocr_used,
            has_extracted_text=bool(upload.extracted_text),
            error_message=upload.error_message,
            created_at=upload.created_at,
        )
    )


@router.delete("/{upload_id}", response_model=APIResponse[None])
async def delete_file(
    upload_id: UUID,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Delete an uploaded file from storage and database."""
    service = FileService(db)
    await service.delete_upload(current_user.id, upload_id)
    return APIResponse(message="File deleted successfully")
