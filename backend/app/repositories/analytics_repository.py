"""
Analytics repository — event tracking and aggregation queries.
"""
from datetime import date, datetime, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import case, cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent, EventType
from app.repositories.base_repository import BaseRepository


class AnalyticsRepository(BaseRepository[AnalyticsEvent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AnalyticsEvent, db)

    async def get_dashboard_aggregates(self, user_id: UUID) -> dict:
        """Fetch the full analytics dashboard's aggregates in one round trip.

        The result is a UNION of independently aggregated, user-scoped reads.
        This keeps the existing calculations while avoiding several serial
        pooler query round trips on the analytics endpoint.
        """
        from sqlalchemy import Date, Float, Integer, String, literal, null, union_all
        from app.models.quiz import QuizAnswer, QuizAttempt, QuizQuestion

        # Keep the same 30/90-day windows and timestamp-to-date casts used by
        # the individual queries. Separate instants also preserve their prior
        # evaluation order to within ordinary query-construction time.
        activity_since = datetime.now(timezone.utc) - timedelta(days=30)
        accuracy_since = datetime.now(timezone.utc) - timedelta(days=30)
        heatmap_since = datetime.now(timezone.utc) - timedelta(days=90)

        summary = select(
            literal("summary", type_=String()).label("kind"),
            cast(null(), Date).label("day"),
            cast(null(), String).label("category"),
            func.count(func.distinct(AnalyticsEvent.topic)).label("topics"),
            func.count(case((AnalyticsEvent.event_type == EventType.summary_generated, 1))).label("summaries"),
            func.count(case((AnalyticsEvent.event_type == EventType.explanation_generated, 1))).label("explanations"),
            func.count(case((AnalyticsEvent.event_type == EventType.quiz_completed, 1))).label("quizzes"),
            cast(null(), Integer).label("total"),
            cast(null(), Integer).label("correct"),
            cast(null(), Float).label("average"),
        ).where(AnalyticsEvent.user_id == user_id)

        def event_activity(kind: str, since: datetime):
            return (
                select(
                    literal(kind, type_=String()).label("kind"),
                    cast(AnalyticsEvent.created_at, Date).label("day"),
                    cast(null(), String).label("category"),
                    cast(null(), Integer).label("topics"),
                    cast(null(), Integer).label("summaries"),
                    cast(null(), Integer).label("explanations"),
                    cast(null(), Integer).label("quizzes"),
                    func.count(AnalyticsEvent.id).label("total"),
                    cast(null(), Integer).label("correct"),
                    cast(null(), Float).label("average"),
                )
                .where(AnalyticsEvent.user_id == user_id)
                .where(AnalyticsEvent.created_at >= since)
                .group_by("day")
            )

        daily_activity = event_activity("daily", activity_since)
        activity_heatmap = event_activity("heatmap", heatmap_since)

        daily_quiz_accuracy = (
            select(
                literal("trend", type_=String()).label("kind"),
                cast(QuizAttempt.created_at, Date).label("day"),
                cast(null(), String).label("category"),
                cast(null(), Integer).label("topics"),
                cast(null(), Integer).label("summaries"),
                cast(null(), Integer).label("explanations"),
                cast(null(), Integer).label("quizzes"),
                cast(null(), Integer).label("total"),
                cast(null(), Integer).label("correct"),
                func.avg(QuizAttempt.percentage).label("average"),
            )
            .where(QuizAttempt.user_id == user_id)
            .where(QuizAttempt.created_at >= accuracy_since)
            .group_by("day")
        )

        category_accuracy = (
            select(
                literal("category", type_=String()).label("kind"),
                cast(null(), Date).label("day"),
                QuizQuestion.category.label("category"),
                cast(null(), Integer).label("topics"),
                cast(null(), Integer).label("summaries"),
                cast(null(), Integer).label("explanations"),
                cast(null(), Integer).label("quizzes"),
                func.count(QuizAnswer.id).label("total"),
                func.sum(case((QuizAnswer.is_correct == True, 1), else_=0)).label("correct"),
                cast(null(), Float).label("average"),
            )
            .join(QuizAnswer, QuizAnswer.question_id == QuizQuestion.id)
            .join(QuizAttempt, QuizAttempt.id == QuizAnswer.attempt_id)
            .where(QuizAttempt.user_id == user_id)
            .where(QuizQuestion.category.isnot(None))
            .group_by(QuizQuestion.category)
        )

        result = await self.db.execute(
            union_all(
                summary,
                daily_activity,
                daily_quiz_accuracy,
                activity_heatmap,
                category_accuracy,
            )
        )

        counts = {"topics": 0, "summaries": 0, "explanations": 0, "quizzes": 0}
        daily_rows: list[dict] = []
        trend_rows: list[dict] = []
        heatmap_rows: list[dict] = []
        category_rows: list[dict] = []
        for row in result:
            if row.kind == "summary":
                counts = {
                    "topics": row.topics or 0,
                    "summaries": row.summaries or 0,
                    "explanations": row.explanations or 0,
                    "quizzes": row.quizzes or 0,
                }
            elif row.kind == "daily":
                daily_rows.append({"date": str(row.day), "count": row.total})
            elif row.kind == "trend":
                trend_rows.append({"date": str(row.day), "count": round(float(row.average or 0), 1)})
            elif row.kind == "heatmap":
                heatmap_rows.append({"date": str(row.day), "count": row.total})
            elif row.kind == "category":
                total = row.total or 0
                correct = int(row.correct or 0)
                category_rows.append({
                    "category": row.category,
                    "total": total,
                    "correct": correct,
                    "accuracy": round((correct / total) * 100, 1) if total else 0.0,
                })

        daily_rows.sort(key=lambda item: item["date"])
        trend_rows.sort(key=lambda item: item["date"])
        heatmap_rows.sort(key=lambda item: item["date"])
        return {
            "counts": counts,
            "category_stats": category_rows,
            "daily_activity": daily_rows,
            "quiz_accuracy_trend": trend_rows,
            "activity_heatmap": heatmap_rows,
        }

    async def log_event(
        self,
        user_id: UUID,
        event_type: EventType,
        topic: str,
        module: str,
        resource_id: str = "",
    ) -> AnalyticsEvent:
        return await self.create_without_refresh(
            user_id=user_id,
            event_type=event_type,
            topic=topic,
            module=module,
            resource_id=resource_id,
        )

    async def get_daily_activity(
        self, user_id: UUID, days: int = 30
    ) -> List[dict]:
        """Topics studied per day for the last N days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(
                cast(AnalyticsEvent.created_at, Date).label("day"),
                func.count(AnalyticsEvent.id).label("count"),
            )
            .where(AnalyticsEvent.user_id == user_id)
            .where(AnalyticsEvent.created_at >= since)
            .group_by("day")
            .order_by("day")
        )
        return [{"date": str(row.day), "count": row.count} for row in result.all()]

    async def count_events_by_type(
        self, user_id: UUID, event_type: EventType
    ) -> int:
        result = await self.db.execute(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == event_type,
            )
        )
        return result.scalar_one()

    async def count_unique_topics(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(AnalyticsEvent.topic))).where(
                AnalyticsEvent.user_id == user_id
            )
        )
        return result.scalar_one()

    async def get_dashboard_summary_counts(self, user_id: UUID) -> dict:
        """Fetch all event-based dashboard totals with one database round trip."""
        result = await self.db.execute(
            select(
                func.count(func.distinct(AnalyticsEvent.topic)).label("topics"),
                func.count(case((AnalyticsEvent.event_type == EventType.summary_generated, 1))).label("summaries"),
                func.count(case((AnalyticsEvent.event_type == EventType.explanation_generated, 1))).label("explanations"),
                func.count(case((AnalyticsEvent.event_type == EventType.quiz_completed, 1))).label("quizzes"),
            ).where(AnalyticsEvent.user_id == user_id)
        )
        row = result.one()
        return {
            "topics": row.topics,
            "summaries": row.summaries,
            "explanations": row.explanations,
            "quizzes": row.quizzes,
        }

    async def get_home_counts_and_activity(self, user_id: UUID, days: int = 7) -> tuple[dict, List[dict]]:
        """Fetch dashboard totals and daily activity with one database round trip."""
        from sqlalchemy import Integer, String, literal, null, union_all

        since = datetime.now(timezone.utc) - timedelta(days=days)
        summary = select(
            literal("summary", type_=String()).label("kind"),
            cast(null(), Date).label("day"),
            func.count(func.distinct(AnalyticsEvent.topic)).label("value1"),
            func.count(case((AnalyticsEvent.event_type == EventType.summary_generated, 1))).label("value2"),
            func.count(case((AnalyticsEvent.event_type == EventType.explanation_generated, 1))).label("value3"),
            func.count(case((AnalyticsEvent.event_type == EventType.quiz_completed, 1))).label("value4"),
        ).where(AnalyticsEvent.user_id == user_id)
        activity = (
            select(
                literal("activity", type_=String()).label("kind"),
                cast(AnalyticsEvent.created_at, Date).label("day"),
                func.count(AnalyticsEvent.id).label("value1"),
                cast(null(), Integer).label("value2"),
                cast(null(), Integer).label("value3"),
                cast(null(), Integer).label("value4"),
            )
            .where(AnalyticsEvent.user_id == user_id)
            .where(AnalyticsEvent.created_at >= since)
            .group_by("day")
        )
        result = await self.db.execute(union_all(summary, activity).order_by("kind", "day"))
        counts = {"topics": 0, "summaries": 0, "explanations": 0, "quizzes": 0}
        daily_activity = []
        for row in result:
            if row.kind == "summary":
                counts = {
                    "topics": row.value1,
                    "summaries": row.value2,
                    "explanations": row.value3,
                    "quizzes": row.value4,
                }
            else:
                daily_activity.append({"date": str(row.day), "count": row.value1})
        return counts, daily_activity

    async def get_activity_heatmap(self, user_id: UUID, days: int = 90) -> List[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(
                cast(AnalyticsEvent.created_at, Date).label("day"),
                func.count(AnalyticsEvent.id).label("count"),
            )
            .where(AnalyticsEvent.user_id == user_id)
            .where(AnalyticsEvent.created_at >= since)
            .group_by("day")
            .order_by("day")
        )
        return [{"date": str(row.day), "count": row.count} for row in result.all()]
