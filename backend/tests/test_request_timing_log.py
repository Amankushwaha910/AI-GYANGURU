"""Tests for secret-free request/timing correlation logs."""

from types import SimpleNamespace

from app import main


def test_request_timing_log_correlates_id_with_server_timing(monkeypatch):
    captured = []
    monkeypatch.setattr(main.logger, "info", lambda *args: captured.append(args))

    timing = "app;dur=7420.0, db;dur=2200.0;desc=\"2 queries\""
    main.log_request_timing(
        "request-id-for-test",
        "GET",
        "/api/v1/dashboard",
        200,
        timing,
    )

    assert len(captured) == 1
    template, *values = captured[0]
    assert "request_id=%s" in template
    assert "server_timing=%s" in template
    assert values == [
        "request-id-for-test",
        "GET",
        "/api/v1/dashboard",
        200,
        timing,
    ]
    assert "Authorization" not in template
    assert "cookie" not in template.lower()


def test_request_route_label_uses_templates_and_hides_unmatched_path():
    matched = SimpleNamespace(scope={"route": SimpleNamespace(path="/api/v1/files/{file_id}")})
    unmatched = SimpleNamespace(scope={"route": None}, url=SimpleNamespace(path="/users/private-value"))

    assert main.request_route_label(matched) == "/api/v1/files/{file_id}"
    assert main.request_route_label(unmatched) == "<unmatched>"
