from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """
    Test GET / root health check.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "service": "semantic-communication"
    }

def test_encode_normal_success():
    """
    Test POST /encode with valid input and normal mode.
    """
    payload = {
        "message": "Send 5 packages to Chennai tomorrow at 3 PM.",
        "mode": "normal"
    }
    response = client.post("/encode", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "semantic_packet" in data
    
    # Assert either the mock packet structure or the real encoded packet structure
    packet = data["semantic_packet"]
    if "message" in packet:
        assert packet["message"] == payload["message"]
    else:
        assert "i" in packet or "o" in packet or "l" in packet
        
    assert "benchmark" in data
    benchmark = data["benchmark"]
    assert "original_bytes" in benchmark
    assert "packet_bytes" in benchmark
    assert "compression_percentage" in benchmark
    assert "encoding_latency_ms" in benchmark
    
    assert benchmark["original_bytes"] == len(payload["message"].encode("utf-8"))
    assert benchmark["packet_bytes"] > 0
    assert benchmark["encoding_latency_ms"] >= 0.0
    assert data["processing_mode"] == "normal"

def test_encode_low_resource_success():
    """
    Test POST /encode with valid input and low_resource mode.
    """
    payload = {
        "message": "Test low resource mode",
        "mode": "low_resource"
    }
    response = client.post("/encode", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["processing_mode"] == "low_resource"

def test_encode_empty_message_validation():
    """
    Test POST /encode with an empty message, which should fail Pydantic validation.
    """
    payload = {
        "message": "",
        "mode": "normal"
    }
    response = client.post("/encode", json=payload)
    assert response.status_code == 422

def test_encode_invalid_mode_validation():
    """
    Test POST /encode with an invalid mode value, which should fail Pydantic validation.
    """
    payload = {
        "message": "Valid message text",
        "mode": "invalid_mode_value"
    }
    response = client.post("/encode", json=payload)
    assert response.status_code == 422

def test_validate_success():
    """
    Test POST /validate with valid payload.
    """
    payload = {
        "original": "Send 5 packages to Chennai tomorrow at 3 PM.",
        "reconstructed": "Decoder integration pending"
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data == {
        "status": "review_required",
        "issues": ["Validator integration pending"]
    }

def test_validate_invalid_payload():
    """
    Test POST /validate with missing required field.
    """
    payload = {
        "original": "Only original text provided"
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 422

def test_decode_endpoint_returns_reconstructed_message():
    """
    Test POST /decode returns reconstructed message.
    """
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
    """
    Test POST /decode accepts low_resource mode.
    """
    response = client.post(
        "/decode",
        json={"packet": {"i": "alert", "w": True}, "mode": "low_resource"},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "low_resource"

def test_decode_endpoint_rejects_invalid_mode():
    """
    Test POST /decode rejects invalid mode with 422.
    """
    response = client.post(
        "/decode",
        json={"packet": {"i": "alert"}, "mode": "turbo"},
    )
    assert response.status_code == 422

def test_decode_endpoint_handles_empty_packet():
    """
    Test POST /decode handles empty packet properly.
    """
    response = client.post("/decode", json={"packet": {}})
    assert response.status_code == 200
    assert response.json()["decoded_message"] == "Process."

def test_get_history():
    """
    Test GET /history endpoint returns saved entries.
    """
    # 1. Trigger an encode request to populate the database
    encode_payload = {
        "message": "Verify database history logging.",
        "mode": "normal"
    }
    encode_res = client.post("/encode", json=encode_payload)
    assert encode_res.status_code == 200

    # 2. Query history
    history_res = client.get("/history")
    assert history_res.status_code == 200
    
    history_data = history_res.json()
    assert isinstance(history_data, list)
    assert len(history_data) > 0
    
    # 3. Verify the latest entry contains correct values
    latest_record = history_data[0]
    assert latest_record["original_message"] == "Verify database history logging."
    assert "semantic_packet" in latest_record
    assert latest_record["processing_mode"] == "normal"
