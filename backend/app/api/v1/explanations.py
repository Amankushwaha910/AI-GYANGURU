"""
Explanation routes — /api/v1/explanations
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.explanation import (
    ExplanationListItem,
    ExplanationResponse,
    GenerateExplanationFromFileRequest,
    GenerateExplanationRequest,
)
from app.services.explanation_service import ExplanationService

router = APIRouter(prefix="/explanations", tags=["Explanations"])


@router.post("", response_model=APIResponse[ExplanationResponse], status_code=201)
async def generate_explanation(
    request: GenerateExplanationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Generate a detailed explanation for a topic."""
    service = ExplanationService(db)
    explanation = await service.generate_from_topic(current_user.id, request)
    return APIResponse(
        data=ExplanationResponse.model_validate(explanation),
        message="Explanation generated successfully",
    )


@router.post("/from-file", response_model=APIResponse[ExplanationResponse], status_code=201)
async def generate_explanation_from_file(
    request: GenerateExplanationFromFileRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Generate an explanation from a previously uploaded file."""
    service = ExplanationService(db)
    explanation = await service.generate_from_file(current_user.id, request)
    return APIResponse(
        data=ExplanationResponse.model_validate(explanation),
        message="Explanation generated from file",
    )


@router.get("", response_model=PaginatedResponse[ExplanationListItem])
async def list_explanations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
):
    service = ExplanationService(db)
    explanations, total = await service.list_explanations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )
    return PaginatedResponse(
        data=[ExplanationListItem.model_validate(e) for e in explanations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/{explanation_id}", response_model=APIResponse[ExplanationResponse])
async def get_explanation(
    explanation_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    service = ExplanationService(db)
    explanation = await service.get_explanation(current_user.id, explanation_id)
    return APIResponse(data=ExplanationResponse.model_validate(explanation))


@router.delete("/{explanation_id}", response_model=APIResponse[None])
async def delete_explanation(
    explanation_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    service = ExplanationService(db)
    await service.delete_explanation(current_user.id, explanation_id)
    return APIResponse(message="Explanation deleted")
