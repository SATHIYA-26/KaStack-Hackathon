from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_decode_endpoint_returns_reconstructed_message():
    response = client.post(
        "/decode",
        json={"packet": {"i": "send", "q": 3, "o": "package", "l": "Chennai"}},
    )
    assert response.status_code == 200

    body = response.json()
    assert "3 packages" in body["decoded_message"]
    assert "chennai" in body["decoded_message"].lower()
    assert body["mode"] == "normal"
    assert body["decoding_latency_ms"] >= 0


def test_decode_endpoint_accepts_low_resource_mode():
    response = client.post(
        "/decode",
        json={"packet": {"i": "alert", "w": True}, "mode": "low_resource"},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "low_resource"


def test_decode_endpoint_rejects_invalid_mode():
    response = client.post(
        "/decode",
        json={"packet": {"i": "alert"}, "mode": "turbo"},
    )
    assert response.status_code == 422


def test_decode_endpoint_handles_empty_packet():
    response = client.post("/decode", json={"packet": {}})
    assert response.status_code == 200
    assert response.json()["decoded_message"] == "Process."
