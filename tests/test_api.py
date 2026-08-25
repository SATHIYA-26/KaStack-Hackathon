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
    assert data["semantic_packet"] == {"message": payload["message"]}
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
    # Pydantic raises validation error for min_length=1, returning 422 Unprocessable Entity
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

def test_decode_success():
    """
    Test POST /decode with valid payload.
    """
    payload = {
        "semantic_packet": {
            "message": "Send 5 packages to Chennai tomorrow at 3 PM."
        }
    }
    response = client.post("/decode", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "reconstructed_message" in data
    assert data["reconstructed_message"] == "Decoder integration pending"
    assert "decoding_latency_ms" in data
    assert data["decoding_latency_ms"] >= 0.0

def test_decode_invalid_payload():
    """
    Test POST /decode with invalid format (semantic_packet must be a dict).
    """
    payload = {
        "semantic_packet": "not a dictionary"
    }
    response = client.post("/decode", json=payload)
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
