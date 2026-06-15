from fastapi.testclient import TestClient

from commerce_search.infrastructure.database.dependencies import get_database_manager
from commerce_search.main import app


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert response.json() == {
        "code": "SUCCESS",
        "message": "Success",
        "data": {"status": "ok"},
        "request_id": request_id,
        "errors": None,
    }


def test_preserves_client_request_id(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health/ready",
        headers={"X-Request-ID": "request-from-gateway"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-from-gateway"
    assert response.json()["request_id"] == "request-from-gateway"


def test_readiness_returns_503_when_database_is_unavailable() -> None:
    class UnavailableDatabase:
        async def ping(self) -> None:
            raise OSError("connection refused")

    app.dependency_overrides[get_database_manager] = lambda: UnavailableDatabase()
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["message"] == "Database is unavailable"
