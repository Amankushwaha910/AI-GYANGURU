"""Single-round-trip reads for the home dashboard."""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Date, String, case, cast, func, literal, select
from sqlalchemy.dialects.postgresql import JSONB, aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent, EventType
from app.models.history import HistoryItem
from app.models.quiz import QuizAnswer, QuizAttempt, QuizQuestion


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_home_dashboard_data(self, user_id: UUID, days: int = 7) -> dict[str, Any]:
        """Return dashboard aggregates and recent history in one SQL round trip."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        event_counts = (
            select(
                func.count(func.distinct(AnalyticsEvent.topic)).label("topics"),
                func.count(
                    case((AnalyticsEvent.event_type == EventType.summary_generated, 1))
                ).label("summaries"),
                func.count(
                    case((AnalyticsEvent.event_type == EventType.explanation_generated, 1))
                ).label("explanations"),
                func.count(
                    case((AnalyticsEvent.event_type == EventType.quiz_completed, 1))
                ).label("quizzes"),
            )
            .where(AnalyticsEvent.user_id == user_id)
            .subquery()
        )
        summary = (
            select(
                cast(
                    func.jsonb_build_object(
                        "topics", event_counts.c.topics,
                        "summaries", event_counts.c.summaries,
                        "explanations", event_counts.c.explanations,
                        "quizzes", event_counts.c.quizzes,
                    ),
                    JSONB,
                )
            )
            .scalar_subquery()
        )

        daily = (
            select(
                cast(AnalyticsEvent.created_at, Date).label("day"),
                func.count(AnalyticsEvent.id).label("count"),
            )
            .where(AnalyticsEvent.user_id == user_id)
            .where(AnalyticsEvent.created_at >= since)
            .group_by("day")
            .subquery()
        )
        daily_item = func.jsonb_build_object(
            "date", cast(daily.c.day, String), "count", daily.c.count
        )
        weekly_activity = (
            select(
                func.coalesce(
                    func.jsonb_agg(aggregate_order_by(daily_item, daily.c.day)),
                    cast(literal("[]"), JSONB),
                )
            )
            .select_from(daily)
            .scalar_subquery()
        )

        quiz_accuracy = (
            select(
                func.count(QuizAnswer.id).label("total"),
                func.coalesce(
                    func.sum(case((QuizAnswer.is_correct == True, 1), else_=0)), 0
                ).label("correct"),
            )
            .select_from(QuizQuestion)
            .join(QuizAnswer, QuizAnswer.question_id == QuizQuestion.id)
            .join(QuizAttempt, QuizAttempt.id == QuizAnswer.attempt_id)
            .where(QuizAttempt.user_id == user_id)
            .where(QuizQuestion.category.isnot(None))
            .subquery()
        )
        accuracy = (
            select(
                cast(
                    func.jsonb_build_object(
                        "total", quiz_accuracy.c.total,
                        "correct", quiz_accuracy.c.correct,
                    ),
                    JSONB,
                )
            )
            .scalar_subquery()
        )

        trend = (
            select(
                cast(QuizAttempt.created_at, Date).label("day"),
                func.avg(QuizAttempt.percentage).label("average"),
            )
            .where(QuizAttempt.user_id == user_id)
            .where(QuizAttempt.created_at >= since)
            .group_by("day")
            .subquery()
        )
        trend_item = func.jsonb_build_object(
            "date", cast(trend.c.day, String), "count", trend.c.average
        )
        quiz_trend = (
            select(
                func.coalesce(
                    func.jsonb_agg(aggregate_order_by(trend_item, trend.c.day)),
                    cast(literal("[]"), JSONB),
                )
            )
            .select_from(trend)
            .scalar_subquery()
        )

        recent = (
            select(
                HistoryItem.id,
                HistoryItem.item_type,
                HistoryItem.topic,
                HistoryItem.resource_id,
                HistoryItem.created_at,
            )
            .where(HistoryItem.user_id == user_id)
            .order_by(HistoryItem.created_at.desc())
            .limit(10)
            .subquery()
        )
        recent_item = func.jsonb_build_object(
            "id", cast(recent.c.id, String),
            "item_type", recent.c.item_type,
            "topic", recent.c.topic,
            "resource_id", recent.c.resource_id,
            "created_at", recent.c.created_at,
        )
        recent_activity = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(recent_item, recent.c.created_at.desc())
                    ),
                    cast(literal("[]"), JSONB),
                )
            )
            .select_from(recent)
            .scalar_subquery()
        )

        result = await self.db.execute(
            select(
                summary.label("summary"),
                weekly_activity.label("weekly_activity"),
                accuracy.label("quiz_accuracy"),
                quiz_trend.label("quiz_accuracy_week"),
                recent_activity.label("recent_activity"),
            )
        )
        row = result.one()
        return {
            "summary": row.summary,
            "weekly_activity": row.weekly_activity,
            "quiz_accuracy": row.quiz_accuracy,
            "quiz_accuracy_week": row.quiz_accuracy_week,
            "recent_activity": row.recent_activity,
        }
