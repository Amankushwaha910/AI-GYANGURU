"""
Dashboard routes — /api/v1/dashboard
Aggregates data from multiple services for the home dashboard view.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.history_repository import HistoryRepository
from app.schemas.analytics import AnalyticsSummary, DailyActivityItem
from app.schemas.common import APIResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class RecentActivityItem(BaseModel):
    id: str
    item_type: str
    topic: str
    resource_id: str
    created_at: datetime


class DashboardResponse(BaseModel):
    summary: AnalyticsSummary
    recent_activity: List[RecentActivityItem]
    weekly_activity: List[DailyActivityItem]
    quiz_accuracy_week: List[DailyActivityItem]


@router.get("", response_model=APIResponse[DashboardResponse])
async def get_dashboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the home dashboard payload:
    - Summary stats (topics, quizzes, accuracy)
    - Recent 10 activity items
    - Weekly activity chart data
    - Quiz accuracy trend (7 days)
    """
    analytics_service = AnalyticsService(db)
    full_dashboard = await analytics_service.get_dashboard(current_user.id)

    # Recent activity — last 10 items
    history_repo = HistoryRepository(db)
    recent_items, _ = await history_repo.get_user_history(
        user_id=current_user.id, page=1, page_size=10
    )

    recent_activity = [
        RecentActivityItem(
            id=str(item.id),
            item_type=item.item_type.value if hasattr(item.item_type, "value") else item.item_type,
            topic=item.topic,
            resource_id=item.resource_id,
            created_at=item.created_at,
        )
        for item in recent_items
    ]

    # Weekly activity = last 7 days of daily_activity
    weekly_activity = full_dashboard.daily_activity[-7:]
    quiz_week = full_dashboard.quiz_accuracy_trend[-7:]

    return APIResponse(
        data=DashboardResponse(
            summary=full_dashboard.summary,
            recent_activity=recent_activity,
            weekly_activity=weekly_activity,
            quiz_accuracy_week=quiz_week,
        )
    )
