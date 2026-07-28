"""
Analytics repository — event tracking and aggregation queries.
"""
from datetime import date, datetime, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent, EventType
from app.repositories.base_repository import BaseRepository


class AnalyticsRepository(BaseRepository[AnalyticsEvent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AnalyticsEvent, db)

    async def log_event(
        self,
        user_id: UUID,
        event_type: EventType,
        topic: str,
        module: str,
        resource_id: str = "",
    ) -> AnalyticsEvent:
        return await self.create(
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
