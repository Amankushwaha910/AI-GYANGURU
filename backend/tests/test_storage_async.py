import asyncio
import time

import pytest

from app.storage.supabase_storage import SupabaseStorageClient


class BlockingBucket:
    def upload(self, **_):
        time.sleep(0.15)

    def create_signed_url(self, path, expires_in):
        time.sleep(0.15)
        return {"signedURL": f"signed:{path}:{expires_in}"}

    def remove(self, paths):
        time.sleep(0.15)
        self.removed = paths


class FakeStorage:
    def __init__(self):
        self.bucket = BlockingBucket()

    def from_(self, _bucket):
        return self.bucket


class FakeClient:
    def __init__(self):
        self.storage = FakeStorage()


async def assert_loop_responsive(awaitable):
    started = time.perf_counter()
    task = asyncio.create_task(awaitable)
    await asyncio.sleep(0.01)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 100
    return await task


@pytest.mark.asyncio
async def test_sync_storage_calls_run_off_event_loop():
    client = SupabaseStorageClient.__new__(SupabaseStorageClient)
    client._client = FakeClient()

    path = await assert_loop_responsive(
        client.upload("bucket", "user", "file.txt", b"content", "text/plain")
    )
    assert path.startswith("users/user/")
    assert path.endswith("_file.txt")

    signed = await assert_loop_responsive(client.get_signed_url("bucket", "object"))
    assert signed == "signed:object:3600"

    await assert_loop_responsive(client.delete("bucket", "object"))
    assert client._client.storage.bucket.removed == ["object"]
