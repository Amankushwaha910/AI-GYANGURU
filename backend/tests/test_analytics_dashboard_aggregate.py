from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects.postgresql import dialect

from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService


def _row(kind, **values):
    fields = {
        "kind": kind,
        "day": None,
        "category": None,
        "topics": None,
        "summaries": None,
        "explanations": None,
        "quizzes": None,
        "total": None,
        "correct": None,
        "average": None,
    }
    fields.update(values)
    return SimpleNamespace(**fields)


@pytest.mark.asyncio
async def test_dashboard_aggregates_use_one_user_scoped_union_query():
    user_id = uuid4()
    rows = [
        _row("summary", topics=3, summaries=2, explanations=1, quizzes=2),
        _row("daily", day=date(2026, 10, 9), total=4),
        _row("trend", day=date(2026, 10, 9), average=75.25),
        _row("heatmap", day=date(2026, 10, 9), total=7),
        _row("category", category="Science", total=4, correct=3),
    ]
    db = SimpleNamespace(execute=AsyncMock(return_value=rows))

    result = await AnalyticsRepository(db).get_dashboard_aggregates(user_id)

    db.execute.assert_awaited_once()
    sql = str(db.execute.await_args.args[0].compile(dialect=dialect()))
    assert sql.count("UNION ALL") == 4
    assert sql.count("analytics_events.user_id =") == 3
    assert sql.count("quiz_attempts.user_id =") == 2
    assert result == {
        "counts": {"topics": 3, "summaries": 2, "explanations": 1, "quizzes": 2},
        "category_stats": [{
            "category": "Science",
            "total": 4,
            "correct": 3,
            "accuracy": 75.0,
        }],
        "daily_activity": [{"date": "2026-10-09", "count": 4}],
        "quiz_accuracy_trend": [{"date": "2026-10-09", "count": 75.2}],
        "activity_heatmap": [{"date": "2026-10-09", "count": 7}],
    }


@pytest.mark.asyncio
async def test_empty_aggregate_result_defaults_to_zero_and_empty_series():
    db = SimpleNamespace(execute=AsyncMock(return_value=[]))

    result = await AnalyticsRepository(db).get_dashboard_aggregates(uuid4())

    assert result == {
        "counts": {"topics": 0, "summaries": 0, "explanations": 0, "quizzes": 0},
        "category_stats": [],
        "daily_activity": [],
        "quiz_accuracy_trend": [],
        "activity_heatmap": [],
    }


@pytest.mark.asyncio
async def test_analytics_service_preserves_summary_trends_and_category_order():
    service = AnalyticsService(SimpleNamespace())
    service.analytics_repo = SimpleNamespace(
        get_dashboard_aggregates=AsyncMock(return_value={
            "counts": {"topics": 3, "summaries": 2, "explanations": 1, "quizzes": 2},
            "category_stats": [
                {"category": "Science", "total": 4, "correct": 3, "accuracy": 75.0},
                {"category": "History", "total": 2, "correct": 0, "accuracy": 0.0},
            ],
            "daily_activity": [{"date": "2026-10-09", "count": 4}],
            "quiz_accuracy_trend": [{"date": "2026-10-09", "count": 75.2}],
            "activity_heatmap": [{"date": "2026-10-09", "count": 7}],
        })
    )

    dashboard = await service.get_dashboard(uuid4())

    assert dashboard.summary.total_topics_studied == 3
    assert dashboard.summary.total_summaries_generated == 2
    assert dashboard.summary.total_explanations_generated == 1
    assert dashboard.summary.total_quizzes_taken == 2
    assert dashboard.summary.overall_quiz_accuracy == 50.0
    assert [item.category for item in dashboard.weak_areas] == ["History", "Science"]
    assert [item.category for item in dashboard.strong_areas] == ["Science", "History"]
    assert dashboard.daily_activity[0].date == date(2026, 10, 9)
    assert dashboard.quiz_accuracy_trend[0].count == 75.2
    assert dashboard.activity_heatmap[0].count == 7
    service.analytics_repo.get_dashboard_aggregates.assert_awaited_once()
