from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks

from app.core.exceptions import FileProcessingError
from app.services.file_service import FileService


def _service():
    service = FileService.__new__(FileService)
    service.db = SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    service.storage = SimpleNamespace(
        upload=AsyncMock(return_value="user/object.txt"),
        delete=AsyncMock(),
    )
    service.upload_repo = SimpleNamespace(create=AsyncMock(), delete=AsyncMock())
    service.analytics_repo = SimpleNamespace(log_event=AsyncMock())
    service.history_repo = SimpleNamespace(add_entry=AsyncMock())
    service._validate_file = AsyncMock(return_value=b"safe test bytes")
    return service


@pytest.mark.asyncio
async def test_upload_database_failure_compensates_remote_object():
    service = _service()
    service.upload_repo.create.side_effect = RuntimeError("database unavailable")
    user_id = uuid4()
    file = SimpleNamespace(filename="test.txt", content_type="text/plain")

    with pytest.raises(RuntimeError, match="database unavailable"):
        await service.upload_and_process(user_id, file, BackgroundTasks())

    service.db.rollback.assert_awaited_once()
    service.storage.delete.assert_awaited_once_with(
        bucket=service.storage.upload.await_args.kwargs["bucket"],
        path="user/object.txt",
    )
    service.analytics_repo.log_event.assert_not_awaited()
    service.history_repo.add_entry.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_cleanup_failure_does_not_hide_original_database_error():
    service = _service()
    service.upload_repo.create.side_effect = RuntimeError("database unavailable")
    service.storage.delete.side_effect = RuntimeError("storage unavailable")
    file = SimpleNamespace(filename="test.txt", content_type="text/plain")

    with pytest.raises(RuntimeError, match="database unavailable"):
        await service.upload_and_process(uuid4(), file, BackgroundTasks())

    service.storage.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_remote_delete_failure_keeps_upload_record_for_retry():
    service = _service()
    upload = SimpleNamespace(storage_path="user/object.txt")
    service.upload_repo.get_user_upload = AsyncMock(return_value=upload)
    service.storage.delete.side_effect = RuntimeError("storage unavailable")

    with pytest.raises(FileProcessingError, match="could not be deleted") as error:
        await service.delete_upload(uuid4(), uuid4())

    assert "storage unavailable" not in error.value.message
    service.db.commit.assert_awaited_once()
    service.upload_repo.delete.assert_not_awaited()
