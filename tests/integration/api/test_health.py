from fastapi.testclient import TestClient


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
