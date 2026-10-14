"""Offline tests for the standalone connection-phase probe helpers."""

import importlib.util
import subprocess
import sys
from pathlib import Path


_PROBE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_connection_phases.py"
_SPEC = importlib.util.spec_from_file_location("probe_connection_phases", _PROBE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe)


def test_attempt_line_reports_nested_phases_as_exclusive_splits():
    record = {
        "attempt": 1,
        "last_completed_phase": "session.connection",
        "result": "ok",
        "asyncpg_connect_ms": 20.0,
        "dialect_connect_ms": 30.0,
        "session_connection_ms": 100.0,
        "first_connect_dispatch_ms": 10.0,
        "connect_event_dispatch_ms": 25.0,
        "codec_calls": {
            "json": [{"elapsed_ms": 10.0}],
            "jsonb": [{"elapsed_ms": 10.0}],
        },
        "introspection_calls": {
            "json": [{"elapsed_ms": 6.0}],
            "jsonb": [{"elapsed_ms": 6.0}],
        },
        "catalog_calls": {
            "json": [{"elapsed_ms": 4.0}],
            "jsonb": [{"elapsed_ms": 4.0}],
        },
    }

    line = probe._attempt_line(record)

    assert "dialect_adapter_exclusive_ms=10.00" in line
    assert "json_introspection_exclusive_ms=2.00" in line
    assert "json_codec_exclusive_ms=4.00" in line
    assert "connect_event_other_exclusive_ms=5.00" in line
    assert "acquisition_unattributed_ms=35.00" in line


def test_supervisor_kills_child_and_preserves_partial_output_on_hard_timeout(
    monkeypatch, capsys
):
    class FakeChild:
        returncode = None

        def __init__(self):
            self.communicate_calls = 0
            self.killed = False

        def communicate(self, timeout):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(cmd="python", timeout=timeout, output="partial stage\n")
            return "partial stage\n", ""

        def kill(self):
            self.killed = True
            self.returncode = -9

    child = FakeChild()
    monkeypatch.setattr(probe.subprocess, "Popen", lambda *args, **kwargs: child)

    result = probe._supervise_child()

    captured = capsys.readouterr().out
    assert result == 124
    assert child.killed
    assert "partial stage" in captured
    assert "probe_result=hard_process_timeout" in captured


def test_probe_bounds_attempts_and_wall_clock():
    assert probe.MAX_ATTEMPTS == 1
    assert probe.OVERALL_BUDGET_SECONDS < 20
    assert probe.CONNECT_TIMEOUT_SECONDS > 0
    assert probe.ACQUISITION_TIMEOUT_SECONDS > 0


def test_safe_import_error_reports_stage_module_and_location_without_message():
    secret_marker = "credential-or-url-must-not-appear"
    try:
        raise ModuleNotFoundError(secret_marker, name="missing_package.submodule")
    except ModuleNotFoundError as exc:
        line = probe._safe_import_error("project_config_import", exc)

    assert "stage=project_config_import" in line
    assert "missing_module=missing_package.submodule" in line
    assert "location=test_connection_phase_probe.py:" in line
    assert secret_marker not in line
    assert "credential" not in line


def test_failure_record_reports_safe_frames_and_deadline_state_without_exception_text():
    secret_marker = "postgres://user:password@example.invalid/db"
    record = {
        "attempt": 1,
        "last_completed_phase": "asyncpg.connect",
        "result": "error",
        "per_acquisition_deadline_fired": True,
        "overall_deadline_fired": False,
        "cancellation_observed": False,
    }
    try:
        raise RuntimeError(secret_marker)
    except RuntimeError as exc:
        probe._record_failure(record, "codec_registration:jsonb", exc)

    line = probe._attempt_line(record)

    assert "error_type=RuntimeError" in line
    assert "failure_phase=codec_registration:jsonb" in line
    assert "per_acquisition_deadline_fired=yes" in line
    assert "overall_deadline_fired=no" in line
    assert "cancellation_observed=no" in line
    assert "test_connection_phase_probe.py:test_failure_record_reports_safe_frames" in line
    assert secret_marker not in line
    assert "password" not in line


def test_cancelled_error_is_recorded_as_cancellation():
    record = {}
    try:
        raise probe.asyncio.CancelledError()
    except probe.asyncio.CancelledError as exc:
        probe._record_failure(record, "session.connection", exc)

    assert record["error_type"] == "CancelledError"
    assert record["cancellation_observed"] is True


def test_exception_chain_includes_safe_cause_context_and_stops_cycles():
    secret_marker = "secret-url-password-token"
    cause = ValueError(secret_marker)
    root = RuntimeError(secret_marker)
    root.__cause__ = cause
    cause.__context__ = root

    details = probe._safe_exception_chain(root)

    assert "root:RuntimeError[" in details
    assert "root_cause:ValueError[" in details
    assert "root_cause_context=cycle" in details
    assert secret_marker not in details


def test_failure_and_connection_state_survive_cleanup_reporting():
    record = {
        "attempt": 1,
        "last_completed_phase": "asyncpg.connect",
        "result": "error",
        "per_acquisition_deadline_fired": True,
        "overall_deadline_fired": False,
        "timeout_cancellation_requested": True,
        "cancellation_observed": False,
        "driver_connection_established": True,
        "pool_invalidate_event_seen": False,
        "pool_close_event_seen": False,
        "failure_connection_state": {
            "phase": "first_connect_initialization",
            "driver_connected": True,
            "invalidated": False,
            "closed": False,
        },
    }
    try:
        raise RuntimeError("sensitive exception content")
    except RuntimeError as exc:
        probe._record_failure(record, "first_connect_initialization", exc)
    record["cleanup_error_type"] = "CancelledError"

    line = probe._attempt_line(record)

    assert "error_type=RuntimeError" in line
    assert "timeout_cancellation_requested=yes" in line
    assert "cancellation_observed=no" in line
    assert "connection_state_at_failure=phase:first_connect_initialization,driver_connected:yes" in line
    assert "pool_close_event_seen=no" in line
    assert "cleanup_error_type=CancelledError" in line
    assert "sensitive exception content" not in line


def test_offline_startup_markers_are_ordered_and_do_not_acquire_database():
    backend_root = _PROBE_PATH.parents[1]
    command = [sys.executable, "-u", "-B", str(_PROBE_PATH), "--offline-startup"]
    timed_out = False
    stderr = ""
    try:
        result = subprocess.run(
            command,
            cwd=backend_root,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        output = result.stdout
        stderr = result.stderr
        assert result.returncode == 0, f"offline startup exit={result.returncode}"
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        output = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    markers = output.splitlines()
    expected = [
        "startup=process_entry",
        "startup=argument_parsing_complete mode=offline",
        "startup=offline_mode_begin",
        "startup=third_party_imports_begin",
        "startup=third_party_imports_complete",
        "startup=performance_import_begin",
        "startup=performance_import_complete",
        "startup=configuration_load_begin",
        "startup=configuration_load_complete",
        "startup=database_module_import_begin",
        "startup=database_module_import_complete",
        "startup=engine_session_factory_setup_begin",
        "startup=engine_session_factory_setup_complete database_connection_attempted=no",
        "startup=runtime_check_complete",
        "startup=event_loop_creation_begin",
    ]
    positions = [next(i for i, line in enumerate(markers) if line.startswith(marker)) for marker in expected]
    assert positions == sorted(positions)
    assert "startup=database_acquisition_begin" not in output
    assert "probe_mode=" not in output
    assert "database_url" not in output.lower()
    assert not stderr
    if timed_out:
        assert markers[-1] == "startup=event_loop_creation_begin"
        assert "startup=event_loop_creation_complete" not in output
    else:
        expected_after_loop = [
            "startup=event_loop_creation_complete",
            "startup=event_loop_closed",
            "startup=asyncio_run_begin",
            "startup=asyncio_coroutine_entry",
            "startup=asyncio_coroutine_complete",
            "startup=asyncio_run_complete",
            "startup=offline_mode_complete database_connection_attempted=no",
        ]
        after_positions = [next(i for i, line in enumerate(markers) if line.startswith(marker)) for marker in expected_after_loop]
        assert after_positions == sorted(after_positions)
