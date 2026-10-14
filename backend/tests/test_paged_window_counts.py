from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects.postgresql import dialect

from app.models.history import HistoryItemType
from app.repositories.history_repository import HistoryRepository
from app.repositories.upload_repository import UploadRepository


@pytest.mark.asyncio
async def test_history_page_and_filtered_total_share_one_statement():
    user_id = uuid4()
    item = object()
    result = SimpleNamespace(all=lambda: [(item, 23)])
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    items, total = await HistoryRepository(db).get_user_history(
        user_id=user_id,
        page=1,
        page_size=20,
        item_type=HistoryItemType.summary,
        search="photosynthesis",
    )

    db.execute.assert_awaited_once()
    sql = str(db.execute.await_args.args[0].compile(dialect=dialect()))
    assert "count(*) OVER" in sql
    assert "history_items.user_id =" in sql
    assert "history_items.item_type =" in sql
    assert "history_items.topic ILIKE" in sql
    assert "history_items.created_at DESC" in sql
    assert items == [item]
    assert total == 23


@pytest.mark.asyncio
async def test_history_empty_out_of_range_page_keeps_exact_total_fallback():
    user_id = uuid4()
    db = SimpleNamespace(execute=AsyncMock(side_effect=[
        SimpleNamespace(all=lambda: []),
        SimpleNamespace(scalar_one=lambda: 23),
    ]))

    items, total = await HistoryRepository(db).get_user_history(
        user_id=user_id, page=3, page_size=20
    )

    assert db.execute.await_count == 2
    assert items == []
    assert total == 23


@pytest.mark.asyncio
async def test_upload_page_and_total_share_one_statement():
    user_id = uuid4()
    item = object()
    result = SimpleNamespace(all=lambda: [(item, 2)])
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    items, total = await UploadRepository(db).get_user_uploads(
        user_id=user_id, page=1, page_size=20
    )

    db.execute.assert_awaited_once()
    sql = str(db.execute.await_args.args[0].compile(dialect=dialect()))
    assert "count(*) OVER" in sql
    assert "uploads.user_id =" in sql
    assert "uploads.created_at DESC" in sql
    assert items == [item]
    assert total == 2


@pytest.mark.asyncio
async def test_upload_empty_page_keeps_exact_total_fallback():
    db = SimpleNamespace(execute=AsyncMock(side_effect=[
        SimpleNamespace(all=lambda: []),
        SimpleNamespace(scalar_one=lambda: 2),
    ]))

    items, total = await UploadRepository(db).get_user_uploads(
        user_id=uuid4(), page=2, page_size=20
    )

    assert db.execute.await_count == 2
    assert items == []
    assert total == 2
