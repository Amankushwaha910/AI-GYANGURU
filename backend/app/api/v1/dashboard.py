"""
Dashboard routes — /api/v1/dashboard
Aggregates data from multiple services for the home dashboard view.
"""
from typing import Any, List
from datetime import datetime
from time import perf_counter

from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserFast
from app.core.performance import add_timing
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.analytics import AnalyticsSummary, DailyActivityItem
from app.schemas.common import APIResponse

class DashboardTimingRoute(APIRoute):
    """Expose route processing time, including FastAPI response serialization."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def timed_handler(request: Request):
            started = perf_counter()
            try:
                return await original_handler(request)
            finally:
                add_timing("dashboard_route_pipeline", (perf_counter() - started) * 1000)

        return timed_handler


class DashboardJSONResponse(JSONResponse):
    """Measure JSON byte rendering without changing the response format."""

    def render(self, content: Any) -> bytes:
        started = perf_counter()
        try:
            return super().render(content)
        finally:
            add_timing("dashboard_json_render", (perf_counter() - started) * 1000)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    route_class=DashboardTimingRoute,
    default_response_class=DashboardJSONResponse,
)


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
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the home dashboard payload:
    - Summary stats (topics, quizzes, accuracy)
    - Recent 10 activity items
    - Weekly activity chart data
    - Quiz accuracy trend (7 days)
    """
    handler_started = perf_counter()
    try:
        dashboard_data = await DashboardRepository(db).get_home_dashboard_data(current_user.id)
        counts = dashboard_data["summary"]
        quiz_accuracy = dashboard_data["quiz_accuracy"]
        total_answered = quiz_accuracy["total"]
        overall_accuracy = (
            round((quiz_accuracy["correct"] / total_answered) * 100, 1)
            if total_answered
            else 0.0
        )
        summary = AnalyticsSummary(
            total_topics_studied=counts["topics"],
            total_summaries_generated=counts["summaries"],
            total_explanations_generated=counts["explanations"],
            total_quizzes_taken=counts["quizzes"],
            overall_quiz_accuracy=overall_accuracy,
        )
        weekly_activity = [
            DailyActivityItem(**item) for item in dashboard_data["weekly_activity"]
        ]
        quiz_week = [
            DailyActivityItem(date=item["date"], count=round(float(item["count"] or 0), 1))
            for item in dashboard_data["quiz_accuracy_week"]
        ]
        recent_activity = [
            RecentActivityItem(**item) for item in dashboard_data["recent_activity"]
        ]

        return APIResponse(
            data=DashboardResponse(
                summary=summary,
                recent_activity=recent_activity,
                weekly_activity=weekly_activity,
                quiz_accuracy_week=quiz_week,
            )
        )
    finally:
        add_timing("dashboard_handler", (perf_counter() - handler_started) * 1000)
