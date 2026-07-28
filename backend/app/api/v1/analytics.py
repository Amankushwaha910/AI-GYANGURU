"""
Analytics routes — /api/v1/analytics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.analytics import AnalyticsDashboard
from app.schemas.common import APIResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=APIResponse[AnalyticsDashboard])
async def get_analytics_dashboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the full analytics dashboard payload:
    summary stats, daily activity, quiz trends, heatmap, weak/strong areas.
    """
    service = AnalyticsService(db)
    dashboard = await service.get_dashboard(current_user.id)
    return APIResponse(data=dashboard)
