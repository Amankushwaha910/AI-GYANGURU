"""Bounded standalone timing probe for the application's asyncpg connect path.

Run from the backend directory with the project virtualenv Python. This creates
one sequential database connection using the same settings and lazy
engine/session factory as the app, but in this separate process. It does not
start or contact the HTTP backend, execute dashboard SQL, print connection
configuration, or change application/database settings. asyncpg's own timeout
is capped only for this diagnostic process.
"""

from __future__ import annotations

import asyncio
import contextvars
import logging
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any


PROCESS_STARTED = time.monotonic()
OVERALL_BUDGET_SECONDS = 19.0
CONNECT_TIMEOUT_SECONDS = 4.5
ACQUISITION_TIMEOUT_SECONDS = 5.2
SESSION_CLOSE_TIMEOUT_SECONDS = 0.3
ENGINE_DISPOSE_TIMEOUT_SECONDS = 0.6
MAX_ATTEMPTS = 1

_record_var: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "connection_phase_probe_record", default=None
)


def _ms(start_ns: int, end_ns: int | None = None) -> float:
    return ((end_ns if end_ns is not None else time.perf_counter_ns()) - start_ns) / 1_000_000


def _current_record() -> dict[str, Any] | None:
    return _record_var.get()


def _phase(record: dict[str, Any], name: str) -> None:
    record["current_phase"] = name


def _completed(record: dict[str, Any], name: str) -> None:
    record["last_completed_phase"] = name
    record["current_phase"] = None


def _safe_traceback_frames(exc: BaseException, limit: int = 8) -> str:
    """Return basename/function/line only; never include source or exception text."""
    frames = traceback.extract_tb(exc.__traceback__)[-limit:]
    if not frames:
        return "unavailable"
    return ",".join(
        f"{Path(frame.filename).name}:{frame.name}:{frame.lineno}" for frame in frames
    )


def _safe_exception_chain(exc: BaseException, max_nodes: int = 8) -> str:
    """Format cause/context graph without messages, locals, source, or paths."""
    pending: list[tuple[str, BaseException]] = [("root", exc)]
    visited: set[int] = set()
    details: list[str] = []
    while pending and len(details) < max_nodes:
        relation, current = pending.pop(0)
        if id(current) in visited:
            details.append(f"{relation}=cycle")
            continue
        visited.add(id(current))
        details.append(
            f"{relation}:{type(current).__name__}[{_safe_traceback_frames(current)}]"
        )
        if current.__cause__ is not None:
            pending.append((f"{relation}_cause", current.__cause__))
        if current.__context__ is not None:
            pending.append((f"{relation}_context", current.__context__))
    if pending:
        details.append("chain=truncated")
    return ";".join(details)


def _record_failure(record: dict[str, Any], phase: str, exc: BaseException) -> None:
    record["failure_phase"] = phase
    record["error_type"] = type(exc).__name__
    record["traceback_frames"] = _safe_traceback_frames(exc)
    record["exception_chain"] = _safe_exception_chain(exc)
    if isinstance(exc, asyncio.CancelledError):
        record["cancellation_observed"] = True


def _runtime_markers() -> None:
    print("startup=runtime_check_begin", flush=True)
    policy = asyncio.get_event_loop_policy()
    print(
        f"startup=runtime_check_complete python={sys.version.split()[0]} "
        f"event_loop_policy={type(policy).__name__}",
        flush=True,
    )


def _load_startup_dependencies() -> dict[str, Any] | None:
    dependencies: dict[str, Any] = {}
    stage = "third_party_imports"
    try:
        print("startup=third_party_imports_begin", flush=True)
        import asyncpg
        import asyncpg.connection
        import asyncpg.introspection
        import sqlalchemy
        from sqlalchemy import event
        dependencies.update(
            asyncpg=asyncpg,
            sqlalchemy=sqlalchemy,
            event=event,
        )
        print("startup=third_party_imports_complete", flush=True)

        stage = "project_performance_import"
        print("startup=performance_import_begin", flush=True)
        from app.core import performance
        dependencies["performance"] = performance
        print("startup=performance_import_complete", flush=True)

        stage = "project_config_import"
        print("startup=configuration_load_begin", flush=True)
        from app.core.config import settings
        dependencies["settings"] = settings
        print("startup=configuration_load_complete", flush=True)

        stage = "project_database_imports"
        print("startup=database_module_import_begin", flush=True)
        from app.core.database import dispose_engine, get_engine, get_session_factory
        dependencies.update(
            dispose_engine=dispose_engine,
            get_engine=get_engine,
            get_session_factory=get_session_factory,
        )
        print("startup=database_module_import_complete", flush=True)
        return dependencies
    except Exception as exc:
        print(_safe_import_error(stage, exc), flush=True)
        return None


async def _offline_sleep() -> None:
    print("startup=asyncio_coroutine_entry", flush=True)
    await asyncio.sleep(0)
    print("startup=asyncio_coroutine_complete", flush=True)


def _offline_startup() -> int:
    """Exercise imports/config/lazy engine setup and event-loop startup only."""
    print("startup=offline_mode_begin", flush=True)
    backend_root = Path(__file__).resolve().parents[1]
    print("startup=working_directory_check_begin", flush=True)
    if Path.cwd().resolve() != backend_root:
        print("probe_error=run_from_backend_directory configuration_not_loaded", flush=True)
        return 2
    print("startup=working_directory_check_complete", flush=True)
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    dependencies = _load_startup_dependencies()
    if dependencies is None:
        return 2

    print("startup=engine_session_factory_setup_begin", flush=True)
    try:
        dependencies["get_engine"]()
        dependencies["get_session_factory"]()
    except Exception as exc:
        print(_safe_import_error("engine_session_factory_setup", exc), flush=True)
        return 2
    print("startup=engine_session_factory_setup_complete database_connection_attempted=no", flush=True)

    _runtime_markers()
    print("startup=event_loop_creation_begin", flush=True)
    loop = asyncio.new_event_loop()
    print("startup=event_loop_creation_complete", flush=True)
    loop.close()
    print("startup=event_loop_closed", flush=True)

    print("startup=asyncio_run_begin", flush=True)
    asyncio.run(_offline_sleep())
    print("startup=asyncio_run_complete", flush=True)
    print("startup=offline_mode_complete database_connection_attempted=no", flush=True)
    return 0


def _safe_import_error(stage: str, exc: BaseException) -> str:
    """Format an import/setup failure without exception text or configuration."""
    frames = traceback.extract_tb(exc.__traceback__)
    location = next(
        (frame for frame in reversed(frames) if not frame.filename.startswith("<")),
        None,
    )
    safe_location = f"{Path(location.filename).name}:{location.lineno}" if location else "unavailable"
    missing_module = (
        getattr(exc, "name", None)
        if isinstance(exc, ModuleNotFoundError)
        else None
    ) or "unavailable"
    return (
        f"probe_error=import_or_setup_failed stage={stage} "
        f"error_type={type(exc).__name__} missing_module={missing_module} "
        f"location={safe_location}"
    )


def _format_ms(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    return f"{key}={value:.2f}" if isinstance(value, (int, float)) else f"{key}=unavailable"


def _attempt_line(record: dict[str, Any]) -> str:
    fields = [
        f"attempt={record['attempt']}",
        "mode=standalone_same_engine_factory",
        f"result={record.get('result', 'incomplete')}",
        f"last_completed={record.get('last_completed_phase', 'none')}",
    ]
    if record.get("failure_phase"):
        fields.append(f"failure_phase={record['failure_phase']}")
    if record.get("error_type"):
        fields.append(f"error_type={record['error_type']}")
    fields.extend((
        f"per_acquisition_deadline_fired={'yes' if record.get('per_acquisition_deadline_fired') else 'no'}",
        f"overall_deadline_fired={'yes' if record.get('overall_deadline_fired') else 'no'}",
        f"cancellation_observed={'yes' if record.get('cancellation_observed') else 'no'}",
    ))
    if record.get("traceback_frames"):
        fields.append(f"traceback_frames={record['traceback_frames']}")
    if record.get("exception_chain"):
        fields.append(f"exception_chain={record['exception_chain']}")
    fields.extend((
        f"timeout_cancellation_requested={'yes' if record.get('timeout_cancellation_requested') else 'no'}",
        f"driver_connection_established={'yes' if record.get('driver_connection_established') else 'no'}",
        f"pool_invalidate_event_seen={'yes' if record.get('pool_invalidate_event_seen') else 'no'}",
        f"pool_close_event_seen={'yes' if record.get('pool_close_event_seen') else 'no'}",
    ))
    failure_state = record.get("failure_connection_state")
    if failure_state:
        fields.append(
            "connection_state_at_failure="
            f"phase:{failure_state['phase']},"
            f"driver_connected:{'yes' if failure_state['driver_connected'] else 'no'},"
            f"invalidate_event:{'seen' if failure_state['invalidated'] else 'not_seen'},"
            f"close_event:{'seen' if failure_state['closed'] else 'not_seen'}"
        )

    for key in (
        "asyncpg_connect_ms",
        "dialect_connect_ms",
        "app_timer_db_connect_ms",
        "app_timer_driver_connect_ms",
        "session_connection_ms",
        "first_connect_dispatch_ms",
        "connect_event_dispatch_ms",
        "session_close_ms",
    ):
        if key in record:
            fields.append(f"{key}={record[key]:.2f}")

    if "asyncpg_connect_ms" in record and "dialect_connect_ms" in record:
        fields.append(
            "dialect_adapter_exclusive_ms="
            f"{max(0.0, record['dialect_connect_ms'] - record['asyncpg_connect_ms']):.2f}"
        )
    if (
        record.get("app_timer_db_connect_ms") is not None
        and record.get("app_timer_driver_connect_ms") is not None
    ):
        fields.append(
            "app_timer_acquisition_other_ms="
            f"{max(0.0, record['app_timer_db_connect_ms'] - record['app_timer_driver_connect_ms']):.2f}"
        )

    codec_totals: dict[str, float] = {}
    for codec in ("json", "jsonb"):
        codec_calls = record.get("codec_calls", {}).get(codec, [])
        introspection_calls = record.get("introspection_calls", {}).get(codec, [])
        catalog_calls = record.get("catalog_calls", {}).get(codec, [])
        if not codec_calls:
            continue
        codec_total = sum(call["elapsed_ms"] for call in codec_calls)
        introspection_total = sum(call["elapsed_ms"] for call in introspection_calls)
        catalog_total = sum(call["elapsed_ms"] for call in catalog_calls)
        codec_totals[codec] = codec_total
        fields.extend(
            (
                f"{codec}_codec_inclusive_ms={codec_total:.2f}",
                f"{codec}_introspection_inclusive_ms={introspection_total:.2f}",
                f"{codec}_catalog_execute_inclusive_ms={catalog_total:.2f}",
                f"{codec}_introspection_exclusive_ms="
                f"{max(0.0, introspection_total - catalog_total):.2f}",
                f"{codec}_codec_exclusive_ms="
                f"{max(0.0, codec_total - introspection_total):.2f}",
            )
        )

    if "connect_event_dispatch_ms" in record and codec_totals:
        fields.append(
            "connect_event_other_exclusive_ms="
            f"{max(0.0, record['connect_event_dispatch_ms'] - sum(codec_totals.values())):.2f}"
        )

    acquisition = record.get("session_connection_ms")
    measured_components = [
        record.get("dialect_connect_ms"),
        record.get("first_connect_dispatch_ms"),
        record.get("connect_event_dispatch_ms"),
    ]
    if acquisition is not None and all(value is not None for value in measured_components):
        residual = acquisition - sum(measured_components)
        fields.append(f"acquisition_unattributed_ms={max(0.0, residual):.2f}")
        if residual < 0:
            fields.append(f"decomposition_mismatch_ms={abs(residual):.2f}")

    for event_name in ("first_connect", "connect_event"):
        started = record.get(f"{event_name}_started_ns")
        if started is not None and f"{event_name}_dispatch_ms" not in record:
            fields.append(f"{event_name}_dispatch_partial_ms={_ms(started):.2f}")

    if record.get("cleanup_error_type"):
        fields.append(f"cleanup_error_type={record['cleanup_error_type']}")
    return " ".join(fields)


async def _run() -> int:
    print("startup=probe_coroutine_entry", flush=True)
    backend_root = Path(__file__).resolve().parents[1]
    print("startup=working_directory_check_begin", flush=True)
    if Path.cwd().resolve() != backend_root:
        print("probe_error=run_from_backend_directory configuration_not_loaded", flush=True)
        return 2
    print("startup=working_directory_check_complete", flush=True)

    # Executing a file under scripts/ puts that directory, not the backend
    # project root, at sys.path[0]. Add the verified backend root so `app` is
    # importable exactly as it is for `python -c` and the project launcher.
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    dependencies = _load_startup_dependencies()
    if dependencies is None:
        return 2
    asyncpg = dependencies["asyncpg"]
    sqlalchemy = dependencies["sqlalchemy"]
    event = dependencies["event"]
    performance = dependencies["performance"]
    settings = dependencies["settings"]
    dispose_engine = dependencies["dispose_engine"]
    get_engine = dependencies["get_engine"]
    get_session_factory = dependencies["get_session_factory"]

    # Suppress SQLAlchemy's optional echo output in this diagnostic process.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)

    original_asyncpg_connect = asyncpg.connect
    original_set_type_codec = asyncpg.connection.Connection.set_type_codec
    original_introspect_type = asyncpg.connection.Connection._introspect_type
    original_execute = asyncpg.connection.Connection._execute
    original_measure_driver = performance.measure_driver_connect
    engine = None
    listeners: list[tuple[Any, str, Any]] = []
    attempt_records: list[dict[str, Any]] = []

    async def timed_asyncpg_connect(*args: Any, **kwargs: Any) -> Any:
        record = _current_record()
        started = time.perf_counter_ns()
        _phase(record, "asyncpg.connect") if record is not None else None
        try:
            configured_timeout = kwargs.get("timeout", CONNECT_TIMEOUT_SECONDS)
            try:
                kwargs["timeout"] = min(float(configured_timeout), CONNECT_TIMEOUT_SECONDS)
            except (TypeError, ValueError):
                kwargs["timeout"] = CONNECT_TIMEOUT_SECONDS
            connection = await original_asyncpg_connect(*args, **kwargs)
            if record is not None:
                record["asyncpg_connect_ms"] = _ms(started)
                record["driver_connection_established"] = True
                _completed(record, "asyncpg.connect")
            return connection
        except BaseException as exc:
            if record is not None:
                record["asyncpg_connect_ms"] = _ms(started)
                _record_failure(record, record.get("current_phase") or "asyncpg.connect", exc)
            raise

    async def timed_execute(self: Any, query: Any, *args: Any, **kwargs: Any) -> Any:
        record = _current_record()
        if record is None or query != asyncpg.introspection.TYPE_BY_OID:
            return await original_execute(self, query, *args, **kwargs)
        codec = record.get("active_codec", "unknown")
        started = time.perf_counter_ns()
        _phase(record, f"catalog_TYPE_BY_OID:{codec}")
        succeeded = False
        try:
            result = await original_execute(self, query, *args, **kwargs)
            succeeded = True
            return result
        except BaseException as exc:
            _record_failure(record, record.get("current_phase") or f"catalog_TYPE_BY_OID:{codec}", exc)
            raise
        finally:
            record.setdefault("catalog_calls", {}).setdefault(codec, []).append(
                {"elapsed_ms": _ms(started), "succeeded": succeeded}
            )
            if succeeded:
                _completed(record, f"catalog_TYPE_BY_OID:{codec}")

    async def timed_introspect_type(
        self: Any, typename: str, schema: str, *args: Any, **kwargs: Any
    ) -> Any:
        record = _current_record()
        if record is None:
            return await original_introspect_type(self, typename, schema, *args, **kwargs)
        started = time.perf_counter_ns()
        _phase(record, f"type_introspection:{typename}")
        succeeded = False
        try:
            result = await original_introspect_type(self, typename, schema, *args, **kwargs)
            succeeded = True
            return result
        except BaseException as exc:
            _record_failure(record, record.get("current_phase") or f"type_introspection:{typename}", exc)
            raise
        finally:
            record.setdefault("introspection_calls", {}).setdefault(typename, []).append(
                {"elapsed_ms": _ms(started), "succeeded": succeeded}
            )
            if succeeded:
                _completed(record, f"type_introspection:{typename}")

    async def timed_set_type_codec(self: Any, typename: str, *args: Any, **kwargs: Any) -> Any:
        record = _current_record()
        if record is None:
            return await original_set_type_codec(self, typename, *args, **kwargs)
        started = time.perf_counter_ns()
        record["active_codec"] = typename
        _phase(record, f"codec_registration:{typename}")
        succeeded = False
        try:
            result = await original_set_type_codec(self, typename, *args, **kwargs)
            succeeded = True
            return result
        except BaseException as exc:
            _record_failure(record, record.get("current_phase") or f"codec_registration:{typename}", exc)
            raise
        finally:
            record.setdefault("codec_calls", {}).setdefault(typename, []).append(
                {"elapsed_ms": _ms(started), "succeeded": succeeded}
            )
            record["active_codec"] = None
            if succeeded:
                _completed(record, f"codec_registration:{typename}")

    def timed_driver_connect(connect: Any) -> Any:
        started = time.perf_counter_ns()
        try:
            return original_measure_driver(connect)
        finally:
            record = _current_record()
            if record is not None:
                record["dialect_connect_ms"] = _ms(started)
                if record.get("failure_phase") is None:
                    _completed(record, "dialect.connect")

    print("startup=diagnostic_wrapper_install_begin", flush=True)
    asyncpg.connect = timed_asyncpg_connect
    asyncpg.connection.Connection.set_type_codec = timed_set_type_codec
    asyncpg.connection.Connection._introspect_type = timed_introspect_type
    asyncpg.connection.Connection._execute = timed_execute
    performance.measure_driver_connect = timed_driver_connect
    print("startup=diagnostic_wrapper_install_complete", flush=True)

    def event_marker(event_name: str, ending: bool):
        def callback(*_args: Any, **_kwargs: Any) -> None:
            record = _current_record()
            if record is None:
                return
            if ending:
                started = record.pop(f"{event_name}_started_ns", None)
                if started is not None:
                    record[f"{event_name}_dispatch_ms"] = _ms(started)
                _completed(record, f"{event_name}_event_dispatch")
            else:
                record[f"{event_name}_started_ns"] = time.perf_counter_ns()
                _phase(record, f"{event_name}_event_dispatch")

        return callback

    def lifecycle_marker(event_name: str):
        def callback(*_args: Any, **_kwargs: Any) -> None:
            record = _current_record()
            if record is not None:
                record[f"pool_{event_name}_event_seen"] = True

        return callback

    try:
        print("startup=engine_session_factory_setup_begin", flush=True)
        engine = get_engine()
        factory = get_session_factory()
        print("startup=engine_session_factory_setup_complete", flush=True)
        print("startup=pool_event_listener_setup_begin", flush=True)

        print(
            f"probe_mode=standalone_same_engine_factory sqlalchemy={sqlalchemy.__version__} "
            f"asyncpg={asyncpg.__version__} pool={type(engine.sync_engine.pool).__name__} "
            f"pool_mode={settings.database_pool_mode} max_attempts={MAX_ATTEMPTS} "
            f"overall_budget_seconds={OVERALL_BUDGET_SECONDS:.1f} "
            f"per_connect_timeout_seconds={CONNECT_TIMEOUT_SECONDS:.1f}",
            flush=True,
        )

        for event_name in ("first_connect", "connect"):
            start_listener = event_marker(event_name, False)
            end_listener = event_marker(event_name, True)
            event.listen(engine.sync_engine.pool, event_name, start_listener, insert=True)
            event.listen(engine.sync_engine.pool, event_name, end_listener)
            listeners.extend(
                ((engine.sync_engine.pool, event_name, start_listener),
                 (engine.sync_engine.pool, event_name, end_listener))
            )

        for event_name in ("invalidate", "close"):
            callback = lifecycle_marker(event_name)
            event.listen(engine.sync_engine.pool, event_name, callback)
            listeners.append((engine.sync_engine.pool, event_name, callback))
        print("startup=pool_event_listener_setup_complete", flush=True)

        async def attempts() -> None:
            for number in range(1, MAX_ATTEMPTS + 1):
                record: dict[str, Any] = {
                    "attempt": number,
                    "last_completed_phase": "none",
                    "failure_phase": None,
                    "codec_calls": {},
                    "introspection_calls": {},
                    "catalog_calls": {},
                    "per_acquisition_deadline_fired": False,
                    "overall_deadline_fired": False,
                    "cancellation_observed": False,
                    "timeout_cancellation_requested": False,
                    "driver_connection_established": False,
                    "pool_invalidate_event_seen": False,
                    "pool_close_event_seen": False,
                }
                attempt_records.append(record)
                record_token = _record_var.set(record)
                request_token = performance.begin_request()
                session = factory()
                acquisition_started, acquisition_token = performance.begin_connection_acquisition()
                connection_started = time.perf_counter_ns()
                try:
                    acquisition_deadline = asyncio.timeout(ACQUISITION_TIMEOUT_SECONDS)
                    async with acquisition_deadline:
                        await session.connection()
                    record["session_connection_ms"] = _ms(connection_started)
                    record["result"] = "ok"
                    _completed(record, "session.connection")
                except BaseException as exc:
                    record["session_connection_ms"] = _ms(connection_started)
                    record["per_acquisition_deadline_fired"] = acquisition_deadline.expired()
                    record["timeout_cancellation_requested"] = acquisition_deadline.expired()
                    record["result"] = "timeout" if isinstance(exc, TimeoutError) else "error"
                    failure_phase = record.get("current_phase") or "session.connection"
                    _record_failure(record, failure_phase, exc)
                    record["failure_connection_state"] = {
                        "phase": failure_phase,
                        "driver_connected": record["driver_connection_established"],
                        "invalidated": record["pool_invalidate_event_seen"],
                        "closed": record["pool_close_event_seen"],
                    }
                    if record["per_acquisition_deadline_fired"]:
                        record["result"] = "timeout"
                finally:
                    performance.finish_connection_acquisition(acquisition_started, acquisition_token)
                    close_started = time.perf_counter_ns()
                    try:
                        await asyncio.wait_for(
                            session.close(), timeout=SESSION_CLOSE_TIMEOUT_SECONDS
                        )
                    except BaseException as exc:
                        record["cleanup_error_type"] = type(exc).__name__
                    record["session_close_ms"] = _ms(close_started)
                    request_timings = performance._request_timings.get() or {}
                    record["app_timer_db_connect_ms"] = request_timings.get("db_connect")
                    record["app_timer_driver_connect_ms"] = request_timings.get("driver_connect")
                    if "session_connection_ms" not in record:
                        record["session_connection_ms"] = request_timings.get("db_connect")
                    record_line = _attempt_line(record)
                    print(record_line, flush=True)
                    performance.end_request(request_token)
                    _record_var.reset(record_token)

                if record.get("result") != "ok":
                    break

        remaining = OVERALL_BUDGET_SECONDS - (time.monotonic() - PROCESS_STARTED)
        run_budget = min(17.0, remaining - 1.0)
        if run_budget <= 0:
            print("probe_result=timeout phase=setup", flush=True)
            return 124
        overall_deadline = asyncio.timeout(run_budget)
        try:
            print("startup=database_acquisition_begin", flush=True)
            async with overall_deadline:
                await attempts()
        except TimeoutError:
            if attempt_records:
                attempt_records[-1]["overall_deadline_fired"] = overall_deadline.expired()
            if not attempt_records or attempt_records[-1].get("result") == "incomplete":
                print("probe_result=overall_timeout overall_deadline_fired=yes last_phase=see_partial_attempt", flush=True)
            elif attempt_records:
                print(f"probe_result=overall_timeout overall_deadline_fired=yes {_attempt_line(attempt_records[-1])}", flush=True)
            return 124
        return 0 if attempt_records and all(r.get("result") == "ok" for r in attempt_records) else 1
    except Exception as exc:
        print(
            f"probe_error=setup_or_event_registration error_type={type(exc).__name__} details=redacted",
            flush=True,
        )
        return 2
    finally:
        for target, event_name, callback in reversed(listeners):
            try:
                event.remove(target, event_name, callback)
            except Exception:
                pass
        asyncpg.connect = original_asyncpg_connect
        asyncpg.connection.Connection.set_type_codec = original_set_type_codec
        asyncpg.connection.Connection._introspect_type = original_introspect_type
        asyncpg.connection.Connection._execute = original_execute
        performance.measure_driver_connect = original_measure_driver
        if engine is not None:
            try:
                await asyncio.wait_for(dispose_engine(), timeout=ENGINE_DISPOSE_TIMEOUT_SECONDS)
                print("engine_dispose=ok", flush=True)
            except BaseException as exc:
                print(f"engine_dispose=error error_type={type(exc).__name__}", flush=True)


def _supervise_child() -> int:
    """Enforce a process-level wall clock bound around async cleanup too."""
    backend_root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != backend_root:
        print("probe_error=run_from_backend_directory configuration_not_loaded", flush=True)
        return 2
    try:
        print("startup=child_process_launch_begin", flush=True)
        child = subprocess.Popen(
            [sys.executable, "-u", "-B", str(Path(__file__).resolve()), "--probe-child"],
            cwd=str(backend_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        print("startup=child_process_launch_complete", flush=True)
    except Exception as exc:
        print(f"probe_error=child_start error_type={type(exc).__name__}", flush=True)
        return 2

    try:
        output, _ = child.communicate(timeout=19.0)
        if output:
            print(output, end="", flush=True)
        return child.returncode if child.returncode is not None else 2
    except subprocess.TimeoutExpired:
        child.kill()
        try:
            output, _ = child.communicate(timeout=0.5)
        except Exception:
            output = ""
        if output:
            print(output, end="", flush=True)
        print(
            "probe_result=hard_process_timeout timeout_seconds=19.0 "
            "child_terminated=windows_process_handle_cleanup=by_os",
            flush=True,
        )
        return 124


if __name__ == "__main__":
    print("startup=process_entry", flush=True)
    print("startup=argument_parsing_begin", flush=True)
    arguments = set(sys.argv[1:])
    if "--offline-startup" in arguments:
        mode = "offline"
    elif "--probe-child" in arguments:
        mode = "probe_child"
    else:
        mode = "supervisor"
    print(f"startup=argument_parsing_complete mode={mode}", flush=True)
    if mode == "offline":
        try:
            exit_code = _offline_startup()
        except BaseException as exc:
            print(f"probe_error=offline_startup error_type={type(exc).__name__} frames={_safe_traceback_frames(exc)}", flush=True)
            exit_code = 2
    elif mode == "probe_child":
        _runtime_markers()
        print("startup=asyncio_run_begin", flush=True)
        try:
            exit_code = asyncio.run(_run())
            print("startup=asyncio_run_complete", flush=True)
        except KeyboardInterrupt:
            print("probe_result=interrupted cleanup=attempted", flush=True)
            exit_code = 130
        except BaseException as exc:
            print(f"probe_error=process error_type={type(exc).__name__} details=redacted", flush=True)
            exit_code = 2
    else:
        exit_code = _supervise_child()
    sys.exit(exit_code)
