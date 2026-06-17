from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from commerce_search.shared.middleware import (
    REQUEST_ID_HEADER,
    RESPONSE_TIME_HEADER,
    RequestContextMiddleware,
)


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RequestContextMiddleware,
        request_id_max_length=32,
    )

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_middleware_preserves_valid_request_id_and_adds_timing() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/test",
            headers={REQUEST_ID_HEADER: "gateway-request-123"},
        )

    assert response.headers[REQUEST_ID_HEADER] == "gateway-request-123"
    assert float(response.headers[RESPONSE_TIME_HEADER]) >= 0


def test_middleware_replaces_invalid_request_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/test",
            headers={REQUEST_ID_HEADER: "invalid request id with spaces"},
        )

    generated_request_id = response.headers[REQUEST_ID_HEADER]
    assert generated_request_id != "invalid request id with spaces"
    assert UUID(generated_request_id)
