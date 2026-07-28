"""
Summary service — orchestrates AI generation, persistence, and history logging.
"""
import uuid
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dispatcher import get_dispatcher
from app.ai.prompt_builder import get_prompt_builder
from app.ai.response_formatter import get_response_formatter
from app.core.exceptions import NotFoundError
from app.core.security import hash_content
from app.models.analytics import EventType
from app.models.history import HistoryItemType
from app.models.summary import Summary
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.summary_repository import SummaryRepository
from app.repositories.upload_repository import UploadRepository
from app.schemas.summary import GenerateSummaryFromFileRequest, GenerateSummaryRequest


class SummaryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.summary_repo = SummaryRepository(db)
        self.upload_repo = UploadRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.history_repo = HistoryRepository(db)
        self.dispatcher = get_dispatcher()
        self.prompt_builder = get_prompt_builder()
        self.formatter = get_response_formatter()

    async def generate_from_topic(
        self, user_id: UUID, request: GenerateSummaryRequest
    ) -> Summary:
        """Generate a summary for a topic using AI."""
        sections = [s.value for s in request.sections]

        messages = self.prompt_builder.build_summary_prompt(
            topic=request.topic,
            sections=sections,
        )

        ai_response, latency = await self.dispatcher.complete(
            messages=messages,
            model=request.model,
            temperature=0.7,
        )

        parsed = self.formatter.extract_json(ai_response.content)
        content = self.formatter.validate_summary_response(parsed, sections)

        word_count = sum(len(v.split()) for v in content.values())

        summary = await self.summary_repo.create(
            user_id=user_id,
            topic=request.topic,
            sections_requested=sections,
            content=content,
            model_used=ai_response.model,
            is_from_file=False,
            word_count=word_count,
        )

        await self._post_generation_hooks(
            user_id=user_id,
            topic=request.topic,
            resource_id=str(summary.id),
        )

        return summary

    async def generate_from_file(
        self, user_id: UUID, request: GenerateSummaryFromFileRequest
    ) -> Summary:
        """Generate a summary from an uploaded file."""
        upload = await self.upload_repo.get_user_upload(user_id, request.upload_id)
        if not upload:
            raise NotFoundError("Upload", str(request.upload_id))

        if not upload.extracted_text:
            raise NotFoundError("Extracted text for upload", str(request.upload_id))

        sections = [s.value for s in request.sections]
        topic = f"Content from: {upload.original_filename}"

        messages = self.prompt_builder.build_summary_prompt(
            topic=topic,
            sections=sections,
            extracted_text=upload.extracted_text,
        )

        ai_response, _ = await self.dispatcher.complete(
            messages=messages,
            model=request.model,
            temperature=0.7,
        )

        parsed = self.formatter.extract_json(ai_response.content)
        content = self.formatter.validate_summary_response(parsed, sections)

        word_count = sum(len(v.split()) for v in content.values())

        summary = await self.summary_repo.create(
            user_id=user_id,
            upload_id=request.upload_id,
            topic=topic,
            sections_requested=sections,
            content=content,
            model_used=ai_response.model,
            is_from_file=True,
            word_count=word_count,
        )

        await self._post_generation_hooks(
            user_id=user_id,
            topic=topic,
            resource_id=str(summary.id),
        )

        return summary

    async def get_summary(self, user_id: UUID, summary_id: UUID) -> Summary:
        summary = await self.summary_repo.get_user_summary(user_id, summary_id)
        if not summary:
            raise NotFoundError("Summary", str(summary_id))
        return summary

    async def list_summaries(
        self, user_id: UUID, page: int, page_size: int, search: Optional[str]
    ) -> Tuple[List[Summary], int]:
        return await self.summary_repo.get_user_summaries(
            user_id=user_id, page=page, page_size=page_size, search=search
        )

    async def delete_summary(self, user_id: UUID, summary_id: UUID) -> None:
        summary = await self.summary_repo.get_user_summary(user_id, summary_id)
        if not summary:
            raise NotFoundError("Summary", str(summary_id))
        await self.summary_repo.delete(summary)

    async def _post_generation_hooks(
        self, user_id: UUID, topic: str, resource_id: str
    ) -> None:
        """Log analytics event and history entry after generation."""
        await self.analytics_repo.log_event(
            user_id=user_id,
            event_type=EventType.summary_generated,
            topic=topic,
            module="summary",
            resource_id=resource_id,
        )
        await self.history_repo.add_entry(
            user_id=user_id,
            item_type=HistoryItemType.summary,
            topic=topic,
            resource_id=resource_id,
        )
