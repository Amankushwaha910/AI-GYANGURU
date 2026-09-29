"""
Summary routes — /api/v1/summaries
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, CurrentUserFast
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.summary import (
    GenerateSummaryFromFileRequest,
    GenerateSummaryRequest,
    SummaryListItem,
    SummaryResponse,
)
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/summaries", tags=["Summaries"])


@router.post("", response_model=APIResponse[SummaryResponse], status_code=201)
async def generate_summary(
    request: GenerateSummaryRequest,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Generate a summary for a topic using AI."""
    service = SummaryService(db)
    summary = await service.generate_from_topic(current_user.id, request)
    return APIResponse(
        data=SummaryResponse.model_validate(summary),
        message="Summary generated successfully",
    )


@router.post("/from-file", response_model=APIResponse[SummaryResponse], status_code=201)
async def generate_summary_from_file(
    request: GenerateSummaryFromFileRequest,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Generate a summary from a previously uploaded file."""
    service = SummaryService(db)
    summary = await service.generate_from_file(current_user.id, request)
    return APIResponse(
        data=SummaryResponse.model_validate(summary),
        message="Summary generated from file",
    )


@router.get("", response_model=PaginatedResponse[SummaryListItem])
async def list_summaries(
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
):
    """List the current user's summaries with pagination and search."""
    service = SummaryService(db)
    summaries, total = await service.list_summaries(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )
    return PaginatedResponse(
        data=[SummaryListItem.model_validate(s) for s in summaries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/{summary_id}", response_model=APIResponse[SummaryResponse])
async def get_summary(
    summary_id: str,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific summary by ID."""
    from uuid import UUID
    service = SummaryService(db)
    summary = await service.get_summary(current_user.id, UUID(summary_id))
    return APIResponse(data=SummaryResponse.model_validate(summary))


@router.delete("/{summary_id}", response_model=APIResponse[None])
async def delete_summary(
    summary_id: str,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Delete a summary."""
    from uuid import UUID
    service = SummaryService(db)
    await service.delete_summary(current_user.id, UUID(summary_id))
    return APIResponse(message="Summary deleted")
