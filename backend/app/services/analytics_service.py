"""
Analytics service — aggregates learning data for dashboard.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import EventType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.quiz_repository import QuizAttemptRepository
from app.repositories.summary_repository import SummaryRepository
from app.schemas.analytics import (
    AnalyticsDashboard,
    AnalyticsSummary,
    CategoryAccuracy,
    DailyActivityItem,
    HistoryTimelineItem,
)


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        self.quiz_attempt_repo = QuizAttemptRepository(db)
        self.summary_repo = SummaryRepository(db)

    async def get_dashboard(self, user_id: UUID) -> AnalyticsDashboard:
        """Compile the full analytics dashboard payload."""

        # Summary stats
        total_topics = await self.analytics_repo.count_unique_topics(user_id)
        total_summaries = await self.analytics_repo.count_events_by_type(
            user_id, EventType.summary_generated
        )
        total_explanations = await self.analytics_repo.count_events_by_type(
            user_id, EventType.explanation_generated
        )
        total_quizzes = await self.analytics_repo.count_events_by_type(
            user_id, EventType.quiz_completed
        )

        # Overall accuracy
        category_stats = await self.quiz_attempt_repo.get_accuracy_by_category(user_id)
        overall_accuracy = 0.0
        if category_stats:
            total_correct = sum(c["correct"] for c in category_stats)
            total_answered = sum(c["total"] for c in category_stats)
            if total_answered > 0:
                overall_accuracy = round((total_correct / total_answered) * 100, 1)

        summary = AnalyticsSummary(
            total_topics_studied=total_topics,
            total_summaries_generated=total_summaries,
            total_explanations_generated=total_explanations,
            total_quizzes_taken=total_quizzes,
            overall_quiz_accuracy=overall_accuracy,
        )

        # Daily activity (last 30 days)
        raw_daily = await self.analytics_repo.get_daily_activity(user_id, days=30)
        daily_activity = [DailyActivityItem(**d) for d in raw_daily]

        # Quiz accuracy trend (last 30 days) — simplified: use attempt percentage per day
        raw_accuracy = await self._get_daily_quiz_accuracy(user_id, days=30)
        quiz_accuracy_trend = [DailyActivityItem(**d) for d in raw_accuracy]

        # Activity heatmap (last 90 days)
        raw_heatmap = await self.analytics_repo.get_activity_heatmap(user_id, days=90)
        activity_heatmap = [DailyActivityItem(**d) for d in raw_heatmap]

        # Weak / strong areas
        sorted_cats = sorted(category_stats, key=lambda x: x["accuracy"])
        weak_areas = [
            CategoryAccuracy(
                category=c["category"],
                accuracy=c["accuracy"],
                attempt_count=c["total"],
            )
            for c in sorted_cats[:5]
        ]
        strong_areas = [
            CategoryAccuracy(
                category=c["category"],
                accuracy=c["accuracy"],
                attempt_count=c["total"],
            )
            for c in sorted_cats[-5:][::-1]
        ]

        return AnalyticsDashboard(
            summary=summary,
            daily_activity=daily_activity,
            quiz_accuracy_trend=quiz_accuracy_trend,
            activity_heatmap=activity_heatmap,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
        )

    async def _get_daily_quiz_accuracy(self, user_id: UUID, days: int) -> list[dict]:
        """Get average quiz accuracy per day."""
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import cast, Date, func, select
        from app.models.quiz import QuizAttempt

        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(
                cast(QuizAttempt.created_at, Date).label("date"),
                func.avg(QuizAttempt.percentage).label("count"),
            )
            .where(QuizAttempt.user_id == user_id)
            .where(QuizAttempt.created_at >= since)
            .group_by("date")
            .order_by("date")
        )
        return [
            {"date": str(row.date), "count": round(float(row.count or 0), 1)}
            for row in result.all()
        ]
