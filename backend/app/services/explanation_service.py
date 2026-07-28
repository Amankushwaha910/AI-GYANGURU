"""
Explanation service.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dispatcher import get_dispatcher
from app.ai.prompt_builder import get_prompt_builder
from app.ai.response_formatter import get_response_formatter
from app.core.exceptions import NotFoundError
from app.models.analytics import EventType
from app.models.explanation import Explanation
from app.models.history import HistoryItemType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.explanation_repository import ExplanationRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.upload_repository import UploadRepository
from app.schemas.explanation import (
    GenerateExplanationFromFileRequest,
    GenerateExplanationRequest,
)


class ExplanationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.explanation_repo = ExplanationRepository(db)
        self.upload_repo = UploadRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.history_repo = HistoryRepository(db)
        self.dispatcher = get_dispatcher()
        self.prompt_builder = get_prompt_builder()
        self.formatter = get_response_formatter()

    async def generate_from_topic(
        self, user_id: UUID, request: GenerateExplanationRequest
    ) -> Explanation:
        messages = self.prompt_builder.build_explanation_prompt(topic=request.topic)

        ai_response, _ = await self.dispatcher.complete(
            messages=messages,
            model=request.model,
            temperature=0.7,
        )

        parsed = self.formatter.extract_json(ai_response.content)
        content = self.formatter.validate_explanation_response(parsed)

        explanation = await self.explanation_repo.create(
            user_id=user_id,
            topic=request.topic,
            content=content,
            model_used=ai_response.model,
            is_from_file=False,
        )

        await self._post_generation_hooks(user_id, request.topic, str(explanation.id))
        return explanation

    async def generate_from_file(
        self, user_id: UUID, request: GenerateExplanationFromFileRequest
    ) -> Explanation:
        upload = await self.upload_repo.get_user_upload(user_id, request.upload_id)
        if not upload or not upload.extracted_text:
            raise NotFoundError("Upload or extracted text", str(request.upload_id))

        topic = f"Content from: {upload.original_filename}"
        messages = self.prompt_builder.build_explanation_prompt(
            topic=topic, extracted_text=upload.extracted_text
        )

        ai_response, _ = await self.dispatcher.complete(
            messages=messages, model=request.model, temperature=0.7
        )

        parsed = self.formatter.extract_json(ai_response.content)
        content = self.formatter.validate_explanation_response(parsed)

        explanation = await self.explanation_repo.create(
            user_id=user_id,
            upload_id=request.upload_id,
            topic=topic,
            content=content,
            model_used=ai_response.model,
            is_from_file=True,
        )

        await self._post_generation_hooks(user_id, topic, str(explanation.id))
        return explanation

    async def get_explanation(self, user_id: UUID, explanation_id: UUID) -> Explanation:
        exp = await self.explanation_repo.get_user_explanation(user_id, explanation_id)
        if not exp:
            raise NotFoundError("Explanation", str(explanation_id))
        return exp

    async def list_explanations(
        self, user_id: UUID, page: int, page_size: int, search: Optional[str]
    ) -> Tuple[List[Explanation], int]:
        return await self.explanation_repo.get_user_explanations(
            user_id=user_id, page=page, page_size=page_size, search=search
        )

    async def delete_explanation(self, user_id: UUID, explanation_id: UUID) -> None:
        exp = await self.explanation_repo.get_user_explanation(user_id, explanation_id)
        if not exp:
            raise NotFoundError("Explanation", str(explanation_id))
        await self.explanation_repo.delete(exp)

    async def _post_generation_hooks(
        self, user_id: UUID, topic: str, resource_id: str
    ) -> None:
        await self.analytics_repo.log_event(
            user_id=user_id,
            event_type=EventType.explanation_generated,
            topic=topic,
            module="explanation",
            resource_id=resource_id,
        )
        await self.history_repo.add_entry(
            user_id=user_id,
            item_type=HistoryItemType.explanation,
            topic=topic,
            resource_id=resource_id,
        )
