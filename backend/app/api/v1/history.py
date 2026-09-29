"""
History routes — /api/v1/history
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, CurrentUserFast
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["History"])


class HistoryItemResponse:
    pass


from pydantic import BaseModel
from datetime import datetime


class HistoryItemOut(BaseModel):
    id: UUID
    item_type: str
    topic: str
    resource_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=PaginatedResponse[HistoryItemOut])
async def get_history(
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    item_type: Optional[str] = Query(
        default=None,
        description="Filter by type: summary, explanation, quiz, upload",
    ),
    search: Optional[str] = Query(default=None, description="Search by topic name"),
):
    """Browse learning history with pagination, type filter, and search."""
    service = HistoryService(db)
    items, total = await service.get_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        item_type=item_type,
        search=search,
    )
    return PaginatedResponse(
        data=[HistoryItemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.delete("/{item_id}", response_model=APIResponse[None])
async def delete_history_item(
    item_id: UUID,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single history item."""
    service = HistoryService(db)
    await service.delete_item(current_user.id, item_id)
    return APIResponse(message="History item deleted")


@router.delete("", response_model=APIResponse[None])
async def clear_history_by_type(
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
    item_type: str = Query(
        ..., description="Type to clear: summary, explanation, quiz, upload"
    ),
):
    """Clear all history items of a specific type."""
    service = HistoryService(db)
    count = await service.clear_by_type(current_user.id, item_type)
    return APIResponse(message=f"Deleted {count} history items of type '{item_type}'")
