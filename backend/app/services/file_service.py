"""
File service — upload, validation, text extraction, OCR pipeline.
"""
import io
import mimetypes
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FileProcessingError, NotFoundError, ValidationError
from app.models.analytics import EventType
from app.models.history import HistoryItemType
from app.models.upload import Upload, UploadStatus
from app.ocr.engine import get_ocr_engine
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.upload_repository import UploadRepository
from app.storage.supabase_storage import get_storage_client


class FileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.upload_repo = UploadRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.history_repo = HistoryRepository(db)
        self.storage = get_storage_client()
        self.ocr_engine = get_ocr_engine()

    async def upload_and_process(
        self,
        user_id: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Upload:
        """
        Upload pipeline:
        1. Validate file (type, size)
        2. Store to Supabase Storage
        3. Create Upload DB record
        4. Queue text extraction as background task
        """
        await self._validate_file(file)

        # Read file content
        content = await file.read()

        # Get file extension
        filename = file.filename or "upload"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Store to cloud storage
        storage_path = await self.storage.upload(
            bucket=settings.supabase_storage_bucket,
            user_id=str(user_id),
            filename=filename,
            content=content,
            mime_type=mime_type,
        )

        # Create DB record
        upload = await self.upload_repo.create(
            user_id=user_id,
            original_filename=filename,
            storage_path=storage_path,
            file_type=ext,
            mime_type=mime_type,
            file_size_bytes=len(content),
            status=UploadStatus.pending,
        )

        # Enqueue background text extraction
        background_tasks.add_task(
            self._extract_text_background,
            upload_id=upload.id,
            content=content,
            file_type=ext,
            mime_type=mime_type,
        )

        # Log analytics
        await self.analytics_repo.log_event(
            user_id=user_id,
            event_type=EventType.file_uploaded,
            topic=filename,
            module="file",
            resource_id=str(upload.id),
        )
        await self.history_repo.add_entry(
            user_id=user_id,
            item_type=HistoryItemType.upload,
            topic=filename,
            resource_id=str(upload.id),
        )

        return upload

    async def _extract_text_background(
        self,
        upload_id: UUID,
        content: bytes,
        file_type: str,
        mime_type: str,
    ) -> None:
        """
        Background task: extract text from file and update Upload record.
        Runs independently from the request/response cycle.
        """
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            upload_repo = UploadRepository(session)
            upload = await upload_repo.get_by_id(upload_id)
            if not upload:
                return

            try:
                await upload_repo.update(upload, status=UploadStatus.processing)
                await session.commit()

                extracted_text, ocr_used = await self._extract_text(
                    content=content,
                    file_type=file_type,
                    mime_type=mime_type,
                )

                await upload_repo.update(
                    upload,
                    extracted_text=extracted_text,
                    ocr_used=ocr_used,
                    status=UploadStatus.completed,
                )
                await session.commit()

            except Exception as exc:
                await upload_repo.update(
                    upload,
                    status=UploadStatus.failed,
                    error_message=str(exc),
                )
                await session.commit()

    async def _extract_text(
        self,
        content: bytes,
        file_type: str,
        mime_type: str,
    ) -> tuple[str, bool]:
        """
        Extract text from file bytes.
        Returns (extracted_text, ocr_used).
        """
        ocr_used = False

        if file_type == "pdf":
            text = self._extract_from_pdf(content)
            # If PDF has no embedded text, use OCR
            if len(text.strip()) < 50:
                text = await self.ocr_engine.extract_from_image(content)
                ocr_used = True

        elif file_type == "docx":
            text = self._extract_from_docx(content)

        elif file_type == "txt":
            text = content.decode("utf-8", errors="ignore")

        elif file_type in ("png", "jpg", "jpeg", "webp"):
            text = await self.ocr_engine.extract_from_image(content)
            ocr_used = True

        else:
            raise FileProcessingError(f"Unsupported file type: {file_type}")

        return text.strip(), ocr_used

    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        """Extract text from PDF using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as exc:
            raise FileProcessingError(f"PDF text extraction failed: {exc}") from exc

    @staticmethod
    def _extract_from_docx(content: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except Exception as exc:
            raise FileProcessingError(f"DOCX text extraction failed: {exc}") from exc

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate file type and size."""
        if not file.filename:
            raise ValidationError("File must have a filename")

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.allowed_extensions_list:
            raise ValidationError(
                f"File type '.{ext}' is not supported. "
                f"Allowed: {', '.join(settings.allowed_extensions_list)}"
            )

        # Read to check size (rewind after)
        content = await file.read()
        await file.seek(0)

        if len(content) > settings.max_file_size_bytes:
            raise ValidationError(
                f"File size exceeds maximum of {settings.max_file_size_mb}MB"
            )

    async def get_upload(self, user_id: UUID, upload_id: UUID) -> Upload:
        upload = await self.upload_repo.get_user_upload(user_id, upload_id)
        if not upload:
            raise NotFoundError("Upload", str(upload_id))
        return upload

    async def list_uploads(self, user_id: UUID, page: int, page_size: int):
        return await self.upload_repo.get_user_uploads(
            user_id=user_id, page=page, page_size=page_size
        )

    async def delete_upload(self, user_id: UUID, upload_id: UUID) -> None:
        upload = await self.upload_repo.get_user_upload(user_id, upload_id)
        if not upload:
            raise NotFoundError("Upload", str(upload_id))

        # Remove from storage
        try:
            await self.storage.delete(
                bucket=settings.supabase_storage_bucket,
                path=upload.storage_path,
            )
        except Exception:
            pass  # Storage deletion failure should not block DB cleanup

        await self.upload_repo.delete(upload)
