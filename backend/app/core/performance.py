"""Per-request timing buckets used to diagnose slow API responses."""
import re
from contextvars import ContextVar, Token
from time import perf_counter
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

_request_timings: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_timings", default=None
)
_connection_acquisition: ContextVar[dict[str, float] | None] = ContextVar(
    "connection_acquisition", default=None
)


def begin_request() -> Token:
    return _request_timings.set(
        {"db_queries": [], "db_gaps": [], "last_query_finished": None, "ai": 0.0, "phases": {}}
    )


def end_request(token: Token) -> None:
    _request_timings.reset(token)


def add_timing(name: str, elapsed_ms: float, label: str | None = None) -> None:
    timings = _request_timings.get()
    if timings is not None:
        if name == "db":
            timings["db_queries"].append((elapsed_ms, label or "SQL"))
        elif name in {
            "db_connect", "driver_connect", "db_acquire_driver",
            "db_acquire_other", "db_commit", "db_rollback", "db_release", "ai",
        }:
            timings[name] = timings.get(name, 0.0) + elapsed_ms
        else:
            phases = timings["phases"]
            phases[name] = phases.get(name, 0.0) + elapsed_ms


def measure_driver_connect(connect: Callable[[], _T]) -> _T:
    """Measure one SQLAlchemy DBAPI connection creation, including failures."""
    started = perf_counter()
    try:
        return connect()
    finally:
        elapsed_ms = (perf_counter() - started) * 1000
        add_timing("driver_connect", elapsed_ms)
        acquisition = _connection_acquisition.get()
        if acquisition is not None:
            acquisition["driver_ms"] += elapsed_ms


def begin_connection_acquisition() -> tuple[float, Token]:
    """Start an outer session.connection span and its nested driver subtotal."""
    started = perf_counter()
    token = _connection_acquisition.set({"driver_ms": 0.0})
    return started, token


def finish_connection_acquisition(started: float, token: Token) -> None:
    """Emit the outer span and a non-overlapping split where measurable."""
    elapsed_ms = (perf_counter() - started) * 1000
    acquisition = _connection_acquisition.get() or {"driver_ms": 0.0}
    _connection_acquisition.reset(token)
    driver_ms = acquisition["driver_ms"]
    add_timing("db_connect", elapsed_ms)
    add_timing("db_acquire_driver", driver_ms)
    remainder_ms = elapsed_ms - driver_ms
    if remainder_ms >= 0:
        add_timing("db_acquire_other", remainder_ms)
    else:
        # Retain an explicit anomaly signal rather than publishing a negative
        # residual if async/context attribution does not fit inside the outer span.
        add_timing("db_acquire_decomposition_mismatch", abs(remainder_ms))


def start_query() -> float:
    started = perf_counter()
    timings = _request_timings.get()
    if timings is not None:
        previous_finished = timings.get("last_query_finished")
        if previous_finished is not None:
            timings["db_gaps"].append((started - previous_finished) * 1000)
    return started


def finish_query(started: float, statement: str, *, failed: bool = False) -> None:
    operation = re.match(r"\s*(SELECT|INSERT|UPDATE|DELETE)", statement, re.IGNORECASE)
    table = re.search(r"\b(?:FROM|INTO|UPDATE)\s+[\"`]?([\w.]+)", statement, re.IGNORECASE)
    label = " ".join(
        part for part in (operation.group(1).upper() if operation else "SQL", table.group(1) if table else "") if part
    )
    add_timing("db", (perf_counter() - started) * 1000, f"{label}{' (failed)' if failed else ''}")
    timings = _request_timings.get()
    if timings is not None:
        timings["last_query_finished"] = perf_counter()


def finish_failed_query(connection: Any, statement: str | None) -> None:
    """Finish an instrumented SQL span from SQLAlchemy's handle_error event."""
    if connection is None or not statement:
        return
    info = getattr(connection, "info", None)
    if info is None:
        return
    started = info.pop("gyanguru_query_started", None)
    if started is not None:
        finish_query(started, statement, failed=True)


def server_timing_header(app_ms: float) -> str:
    timings = _request_timings.get() or {}
    parts = [f"app;dur={app_ms:.1f}"]
    queries = timings.get("db_queries", [])
    if queries:
        parts.append(f'db;dur={sum(duration for duration, _ in queries):.1f};desc="{len(queries)} queries"')
        for index, (duration, label) in enumerate(queries, start=1):
            parts.append(f'dbq{index};dur={duration:.1f};desc="{label}"')
    for index, duration in enumerate(timings.get("db_gaps", []), start=1):
        parts.append(f"dbgap{index};dur={duration:.1f}")
    if timings.get("db_connect"):
        parts.append(f"db_connect;dur={timings['db_connect']:.1f}")
    if timings.get("driver_connect"):
        parts.append(f"driver_connect;dur={timings['driver_connect']:.1f}")
    for name in ("db_acquire_driver", "db_acquire_other", "db_acquire_decomposition_mismatch"):
        if timings.get(name):
            parts.append(f"{name};dur={timings[name]:.1f}")
    if timings.get("db_commit"):
        parts.append(f"db_commit;dur={timings['db_commit']:.1f}")
    if timings.get("db_rollback"):
        parts.append(f"db_rollback;dur={timings['db_rollback']:.1f}")
    if timings.get("db_release"):
        parts.append(f"db_release;dur={timings['db_release']:.1f}")
    if timings.get("ai"):
        parts.append(f"ai;dur={timings['ai']:.1f}")
    for name, duration in timings.get("phases", {}).items():
        parts.append(f"{name};dur={duration:.1f}")
    return ", ".join(parts)
