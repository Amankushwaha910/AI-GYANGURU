"""
Analytics service — aggregates learning data for dashboard.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
        aggregates = await self.analytics_repo.get_dashboard_aggregates(user_id)
        counts = aggregates["counts"]
        category_stats = aggregates["category_stats"]
        overall_accuracy = 0.0
        if category_stats:
            total_correct = sum(c["correct"] for c in category_stats)
            total_answered = sum(c["total"] for c in category_stats)
            if total_answered > 0:
                overall_accuracy = round((total_correct / total_answered) * 100, 1)

        summary = AnalyticsSummary(
            total_topics_studied=counts["topics"],
            total_summaries_generated=counts["summaries"],
            total_explanations_generated=counts["explanations"],
            total_quizzes_taken=counts["quizzes"],
            overall_quiz_accuracy=overall_accuracy,
        )

        daily_activity = [
            DailyActivityItem(**item) for item in aggregates["daily_activity"]
        ]
        quiz_accuracy_trend = [
            DailyActivityItem(**item) for item in aggregates["quiz_accuracy_trend"]
        ]
        activity_heatmap = [
            DailyActivityItem(**item) for item in aggregates["activity_heatmap"]
        ]

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

    async def get_home_dashboard(self, user_id: UUID):
        """Build only the data shown on the home page, skipping analytics-only data."""
        counts, raw_activity = await self.analytics_repo.get_home_counts_and_activity(
            user_id, days=7
        )
        total_answered, total_correct, raw_accuracy = (
            await self.quiz_attempt_repo.get_home_accuracy_and_trend(user_id, days=7)
        )
        accuracy = (
            round((total_correct / total_answered) * 100, 1)
            if total_answered
            else 0.0
        )
        summary = AnalyticsSummary(
            total_topics_studied=counts["topics"],
            total_summaries_generated=counts["summaries"],
            total_explanations_generated=counts["explanations"],
            total_quizzes_taken=counts["quizzes"],
            overall_quiz_accuracy=accuracy,
        )
        weekly_activity = [DailyActivityItem(**d) for d in raw_activity]
        weekly_accuracy = [DailyActivityItem(**d) for d in raw_accuracy]
        return summary, weekly_activity, weekly_accuracy
