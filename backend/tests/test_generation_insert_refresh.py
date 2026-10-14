"""Regression tests for generation inserts that use INSERT RETURNING."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect

from app.models.analytics import EventType
from app.models.history import HistoryItemType
from app.models.analytics import AnalyticsEvent
from app.models.explanation import Explanation
from app.models.history import HistoryItem
from app.models.summary import Summary
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.explanation_repository import ExplanationRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.summary_repository import SummaryRepository
from app.repositories.base_repository import BaseRepository
from app.schemas.explanation import ExplanationResponse
from app.schemas.summary import SummaryResponse


def _run_immediate(coroutine):
    """Run these no-I/O repository coroutines without creating an event loop."""
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    raise AssertionError("repository coroutine unexpectedly suspended")


class _FlushOnlySession:
    def __init__(self):
        self.added = []
        self.flush_count = 0

    def add(self, instance):
        self.added.append(instance)

    async def flush(self):
        self.flush_count += 1

    async def refresh(self, _instance):
        raise AssertionError("generation insert must not issue a refresh")


class _RefreshSession(_FlushOnlySession):
    def __init__(self):
        super().__init__()
        self.refresh_count = 0

    async def refresh(self, _instance):
        self.refresh_count += 1


def test_generation_repository_inserts_flush_without_refresh():
    session = _FlushOnlySession()
    user_id = uuid4()
    cases = (
        (
            SummaryRepository,
            {
                "user_id": user_id,
                "topic": "test topic",
                "sections_requested": [],
                "content": {},
                "model_used": "test",
                "is_from_file": False,
                "word_count": 0,
            },
        ),
        (
            ExplanationRepository,
            {
                "user_id": user_id,
                "topic": "test topic",
                "content": {},
                "model_used": "test",
                "is_from_file": False,
            },
        ),
        (
            AnalyticsRepository,
            {
                "user_id": user_id,
                "event_type": EventType.summary_generated,
                "topic": "test topic",
                "module": "summary",
                "resource_id": str(uuid4()),
            },
        ),
        (
            HistoryRepository,
            {
                "user_id": user_id,
                "item_type": HistoryItemType.summary,
                "topic": "test topic",
                "resource_id": str(uuid4()),
            },
        ),
    )

    for repository_type, values in cases:
        result = _run_immediate(
            repository_type(session).create_without_refresh(**values)
        )
        assert result is session.added[-1]

    assert len(session.added) == 4
    assert session.flush_count == 4


def test_generation_models_fetch_insert_defaults_during_postgresql_flush():
    dialect = postgresql_dialect()
    models = (Summary, Explanation, AnalyticsEvent, HistoryItem)

    assert dialect.insert_returning
    for model in models:
        mapper = model.__mapper__
        assert mapper.eager_defaults == "auto"
        assert mapper.persist_selectable.implicit_returning
        assert mapper.primary_key[0].default is not None
        for field in ("created_at", "updated_at"):
            assert mapper.columns[field].server_default is not None


def test_generic_create_still_refreshes_after_flush():
    session = _RefreshSession()
    repository = BaseRepository(Summary, session)

    result = _run_immediate(
        repository.create(
            user_id=uuid4(),
            topic="generic create",
            sections_requested=[],
            content={},
            model_used="test",
            is_from_file=False,
            word_count=0,
        )
    )

    assert result is session.added[0]
    assert session.flush_count == 1
    assert session.refresh_count == 1


def test_generation_response_schemas_read_inserted_model_fields():
    created_at = datetime.now(timezone.utc)
    summary = Summary(
        id=uuid4(),
        user_id=uuid4(),
        topic="test summary",
        sections_requested=["definition"],
        content={"definition": "A test."},
        model_used="test-model",
        is_from_file=False,
        word_count=2,
        created_at=created_at,
        updated_at=created_at,
    )
    explanation = Explanation(
        id=uuid4(),
        user_id=uuid4(),
        topic="test explanation",
        content={"introduction": "A test."},
        model_used="test-model",
        is_from_file=False,
        created_at=created_at,
        updated_at=created_at,
    )

    summary_response = SummaryResponse.model_validate(summary)
    explanation_response = ExplanationResponse.model_validate(explanation)

    assert summary_response.id == summary.id
    assert summary_response.created_at == created_at
    assert summary_response.content == summary.content
    assert explanation_response.id == explanation.id
    assert explanation_response.created_at == created_at
    assert explanation_response.content == explanation.content
