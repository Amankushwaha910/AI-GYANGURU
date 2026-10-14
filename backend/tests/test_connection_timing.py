import re
import asyncio
from types import SimpleNamespace

import pytest

from app.core.performance import (
    begin_request,
    begin_connection_acquisition,
    end_request,
    finish_connection_acquisition,
    finish_failed_query,
    measure_driver_connect,
    start_query,
    server_timing_header,
)


def _metric_duration(header: str, name: str) -> float:
    match = re.search(rf"(?:^|, ){name};dur=([0-9.]+)", header)
    assert match is not None
    return float(match.group(1))


def test_driver_connect_timing_is_exposed_for_success():
    token = begin_request()
    try:
        marker = object()
        assert measure_driver_connect(lambda: marker) is marker
        header = server_timing_header(10.0)
        assert _metric_duration(header, "driver_connect") >= 0.0
        assert "db_connect" not in header
    finally:
        end_request(token)


def test_driver_connect_timing_is_exposed_when_creation_fails():
    token = begin_request()
    try:
        with pytest.raises(ConnectionError, match="private detail"):
            measure_driver_connect(
                lambda: (_ for _ in ()).throw(ConnectionError("private detail"))
            )

        header = server_timing_header(10.0)
        assert _metric_duration(header, "driver_connect") >= 0.0
        assert "private detail" not in header
    finally:
        end_request(token)


def test_db_commit_timing_is_exposed_without_changing_other_spans():
    token = begin_request()
    try:
        from app.core.performance import add_timing

        add_timing("db_commit", 12.5)
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db_commit") == 12.5
        assert "db_connect" not in header
    finally:
        end_request(token)


def test_acquisition_split_reports_nested_driver_and_non_overlapping_remainder(monkeypatch):
    ticks = iter([10.0, 10.001, 10.003, 10.010])
    monkeypatch.setattr("app.core.performance.perf_counter", lambda: next(ticks))
    request_token = begin_request()
    try:
        outer_started, acquisition_token = begin_connection_acquisition()
        measure_driver_connect(lambda: "connection")
        finish_connection_acquisition(outer_started, acquisition_token)
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db_connect") == 10.0
        assert _metric_duration(header, "driver_connect") == 2.0
        assert _metric_duration(header, "db_acquire_driver") == 2.0
        assert _metric_duration(header, "db_acquire_other") == 8.0
    finally:
        end_request(request_token)


def test_failed_sql_span_is_finished_without_exposing_error_or_parameters(monkeypatch):
    ticks = iter([2.004, 2.005])
    monkeypatch.setattr("app.core.performance.perf_counter", lambda: next(ticks))
    request_token = begin_request()
    connection = SimpleNamespace(info={"gyanguru_query_started": 1.0})
    try:
        finish_failed_query(connection, "SELECT * FROM users WHERE email = 'private@example.test'")
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db") == 1004.0
        assert 'desc="SELECT users (failed)"' in header
        assert "private@example.test" not in header
        assert "gyanguru_query_started" not in connection.info
    finally:
        end_request(request_token)


class _FakeSession:
    def __init__(self, *, connection_error=None, commit_error=None, close_error=None):
        self.connection_error = connection_error
        self.commit_error = commit_error
        self.close_error = close_error
        self.calls = []

    async def connection(self):
        self.calls.append("connection")
        if self.connection_error:
            raise self.connection_error

    async def commit(self):
        self.calls.append("commit")
        if self.commit_error:
            raise self.commit_error

    async def rollback(self):
        self.calls.append("rollback")

    async def close(self):
        self.calls.append("close")
        if self.close_error:
            raise self.close_error


class _FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *args):
        return False


def _drive(awaitable):
    """Drive the fake-session coroutine without starting a Windows event loop."""
    try:
        return awaitable.send(None)
    except StopIteration as completed:
        return completed.value


def _run_dependency(monkeypatch, session):
    from app.core import database

    class Factory:
        def __call__(self):
            return _FakeSessionContext(session)

    monkeypatch.setattr(database, "get_session_factory", lambda: Factory())

    dependency = database.get_db()
    _drive(dependency.asend(None))
    with pytest.raises(StopAsyncIteration):
        _drive(dependency.asend(None))


def test_dependency_success_times_connection_commit_and_release(monkeypatch):
    request_token = begin_request()
    session = _FakeSession()
    try:
        _run_dependency(monkeypatch, session)
        header = server_timing_header(20.0)
        for metric in ("db_connect", "db_acquire_other", "db_commit", "db_release"):
            assert _metric_duration(header, metric) >= 0.0
        assert session.calls == ["connection", "commit", "close"]
    finally:
        end_request(request_token)


def test_dependency_acquisition_failure_times_outer_span_rolls_back_and_releases(monkeypatch):
    request_token = begin_request()
    session = _FakeSession(connection_error=ConnectionError("private connection details"))
    try:
        from app.core import database

        class Factory:
            def __call__(self):
                return _FakeSessionContext(session)

        monkeypatch.setattr(database, "get_session_factory", lambda: Factory())
        dependency = database.get_db()
        with pytest.raises(ConnectionError):
            _drive(dependency.asend(None))
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db_connect") >= 0.0
        assert _metric_duration(header, "db_rollback") >= 0.0
        assert _metric_duration(header, "db_release") >= 0.0
        assert "private connection details" not in header
        assert session.calls == ["connection", "rollback", "close"]
    finally:
        end_request(request_token)


def test_dependency_commit_failure_times_finalization_rollback_and_release(monkeypatch):
    request_token = begin_request()
    session = _FakeSession(commit_error=RuntimeError("private commit details"))
    try:
        with pytest.raises(RuntimeError):
            _run_dependency(monkeypatch, session)
        header = server_timing_header(20.0)
        for metric in ("db_commit", "db_rollback", "db_release"):
            assert _metric_duration(header, metric) >= 0.0
        assert "private commit details" not in header
        assert session.calls == ["connection", "commit", "rollback", "close"]
    finally:
        end_request(request_token)


def test_dependency_cancellation_keeps_existing_no_rollback_behavior_and_releases(monkeypatch):
    from app.core import database

    request_token = begin_request()
    session = _FakeSession()

    class Factory:
        def __call__(self):
            return _FakeSessionContext(session)

    monkeypatch.setattr(database, "get_session_factory", lambda: Factory())
    dependency = database.get_db()
    try:
        _drive(dependency.asend(None))
        with pytest.raises(asyncio.CancelledError):
            _drive(dependency.athrow(asyncio.CancelledError()))
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db_connect") >= 0.0
        assert _metric_duration(header, "db_release") >= 0.0
        assert "db_rollback" not in header
        assert session.calls == ["connection", "close"]
    finally:
        end_request(request_token)


def test_dependency_release_failure_still_emits_release_timing(monkeypatch):
    from app.core import database

    request_token = begin_request()
    session = _FakeSession(close_error=RuntimeError("private close details"))

    class Factory:
        def __call__(self):
            return _FakeSessionContext(session)

    monkeypatch.setattr(database, "get_session_factory", lambda: Factory())
    dependency = database.get_db()
    try:
        _drive(dependency.asend(None))
        with pytest.raises(RuntimeError):
            _drive(dependency.asend(None))
        header = server_timing_header(20.0)
        assert _metric_duration(header, "db_release") >= 0.0
        assert "private close details" not in header
    finally:
        end_request(request_token)
