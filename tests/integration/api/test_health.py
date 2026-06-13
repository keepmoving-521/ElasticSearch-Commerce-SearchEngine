from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_preserves_client_request_id(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health/ready",
        headers={"X-Request-ID": "request-from-gateway"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-from-gateway"
