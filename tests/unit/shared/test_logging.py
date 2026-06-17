from commerce_search.shared.logging import (
    add_service_context,
    redact_sensitive_values,
)


def test_sensitive_log_values_are_redacted() -> None:
    event = {
        "event": "login_failed",
        "password": "plain-text",
        "Authorization": "Bearer secret-token",
        "user_id": "123",
    }

    result = redact_sensitive_values(None, "info", event)

    assert result["password"] == "[REDACTED]"
    assert result["Authorization"] == "[REDACTED]"
    assert result["user_id"] == "123"


def test_service_context_is_added_without_overwriting_event_values() -> None:
    processor = add_service_context("commerce-search", "test")

    result = processor(
        None,
        "info",
        {"event": "started", "environment": "override"},
    )

    assert result["service"] == "commerce-search"
    assert result["environment"] == "override"
