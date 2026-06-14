from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

from commerce_search.api.exception_handlers import register_exception_handlers
from commerce_search.shared.exceptions import ResourceNotFoundError
from commerce_search.shared.middleware import RequestContextMiddleware


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/validation")
    async def validation_endpoint(
        quantity: Annotated[int, Query(ge=1)],
    ) -> dict[str, int]:
        return {"quantity": quantity}

    @app.get("/business-error")
    async def business_error_endpoint() -> None:
        raise ResourceNotFoundError(
            "Product was not found",
            code="PRODUCT_NOT_FOUND",
        )

    @app.get("/unexpected-error")
    async def unexpected_error_endpoint() -> None:
        raise RuntimeError("database credentials must not leak")

    return app


def test_validation_error_uses_standard_response() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/validation", params={"quantity": 0})

    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert body["data"] is None
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["errors"][0]["field"] == "query.quantity"


def test_business_error_uses_custom_business_code() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get(
            "/business-error",
            headers={"X-Request-ID": "business-request"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "code": "PRODUCT_NOT_FOUND",
        "message": "Product was not found",
        "data": None,
        "request_id": "business-request",
        "errors": None,
    }


def test_framework_http_error_uses_standard_response() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["data"] is None


def test_unexpected_error_hides_internal_details() -> None:
    with TestClient(create_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected-error")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert response.json()["message"] == "Internal server error"
    assert "credentials" not in response.text
