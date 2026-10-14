from types import SimpleNamespace

import pytest

from app.core.exceptions import ValidationError
from app.services import file_service as file_service_module
from app.services.file_service import FileService


class FakeUploadFile:
    def __init__(self, content: bytes, *, size=None):
        self.filename = "notes.txt"
        self.size = size
        self.content = content
        self.read_limits = []
        self.position = 0

    async def read(self, size=-1):
        self.read_limits.append(size)
        if size < 0:
            result = self.content[self.position:]
        else:
            result = self.content[self.position:self.position + size]
        self.position += len(result)
        return result

    async def seek(self, position):
        self.position = position


@pytest.fixture
def small_upload_limit(monkeypatch):
    monkeypatch.setattr(
        file_service_module,
        "settings",
        SimpleNamespace(
            allowed_extensions_list=["txt"],
            max_file_size_bytes=10,
            max_file_size_mb=1,
        ),
    )


@pytest.mark.asyncio
async def test_file_validation_reads_only_bounded_bytes(small_upload_limit):
    service = object.__new__(FileService)
    upload = FakeUploadFile(b"0123456789ABCDEF", size=None)

    with pytest.raises(ValidationError, match="exceeds maximum"):
        await service._validate_file(upload)

    assert upload.read_limits == [11]


@pytest.mark.asyncio
async def test_file_validation_rejects_declared_oversize_without_reading(small_upload_limit):
    service = object.__new__(FileService)
    upload = FakeUploadFile(b"0123456789ABCDEF", size=11)

    with pytest.raises(ValidationError, match="exceeds maximum"):
        await service._validate_file(upload)

    assert upload.read_limits == []


@pytest.mark.asyncio
async def test_file_validation_returns_allowed_content_and_rewinds(small_upload_limit):
    service = object.__new__(FileService)
    upload = FakeUploadFile(b"safe", size=4)

    assert await service._validate_file(upload) == b"safe"
    assert upload.read_limits == [11]
    assert upload.position == 0
