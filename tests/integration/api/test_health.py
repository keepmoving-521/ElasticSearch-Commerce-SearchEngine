import asyncio

from fastapi.testclient import TestClient

from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.dependencies import (
    get_app_settings,
    get_infrastructure_clients,
)
from commerce_search.main import app
from commerce_search.shared.config import Environment, Settings


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
    assert set(response.json()["data"]["components"]) == {
        "database",
        "elasticsearch",
        "redis",
        "kafka",
    }
    assert all(
        component["latency_ms"] >= 0 for component in response.json()["data"]["components"].values()
    )


def test_readiness_reports_unavailable_dependencies() -> None:
    class HealthyClient:
        async def ping(self) -> None:
            return None

    class UnavailableClient:
        async def ping(self) -> None:
            raise OSError("connection refused")

    clients = InfrastructureClients(
        database=UnavailableClient(),  # type: ignore[arg-type]
        elasticsearch=HealthyClient(),  # type: ignore[arg-type]
        redis=UnavailableClient(),  # type: ignore[arg-type]
        kafka=HealthyClient(),  # type: ignore[arg-type]
    )
    app.dependency_overrides[get_infrastructure_clients] = lambda: clients
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["code"] == "INFRASTRUCTURE_UNAVAILABLE"
    assert {error["field"] for error in response.json()["errors"]} == {
        "database",
        "redis",
    }


def test_readiness_times_out_slow_dependency() -> None:
    class HealthyClient:
        async def ping(self) -> None:
            return None

    class SlowClient:
        async def ping(self) -> None:
            await asyncio.sleep(0.1)

    clients = InfrastructureClients(
        database=HealthyClient(),  # type: ignore[arg-type]
        elasticsearch=SlowClient(),  # type: ignore[arg-type]
        redis=HealthyClient(),  # type: ignore[arg-type]
        kafka=HealthyClient(),  # type: ignore[arg-type]
    )
    settings = Settings(
        _env_file=None,
        environment=Environment.TEST,
        health_check_timeout_seconds=0.01,
    )
    app.dependency_overrides[get_infrastructure_clients] = lambda: clients
    app.dependency_overrides[get_app_settings] = lambda: settings
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["errors"] == [
        {
            "field": "elasticsearch",
            "message": "Dependency health check timed out",
            "type": "TimeoutError",
        }
    ]
