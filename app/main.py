import json
import time
from fastapi import FastAPI, HTTPException
from app.models import EncodeRequest, DecodeRequest, DecodeResponse, ValidateRequest
from app.decoder import decode_packet
from app.database import (
    init_db,
    save_message,
    update_message_decoding,
    update_message_validation,
    get_history
)

# Automatically initialize database tables on startup
init_db()

# Graceful dynamic import of the encoder to prevent crashes if spaCy is not installed
try:
    from app.encoder import semantic_encode
    HAS_ENCODER = True
except (ImportError, ModuleNotFoundError):
    HAS_ENCODER = False

app = FastAPI(
    title="Semantic Communication Backend",
    description="Backend API layer with benchmarking and database storage for the Semantic Communication System.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """
    Health check and service status endpoint.
    """
    return {
        "status": "running",
        "service": "semantic-communication"
    }

@app.get("/history")
def read_history(limit: int = 100):
    """
    Retrieves the history of message transmissions and benchmarks from the database.
    """
    return get_history(limit=limit)

@app.post("/encode")
def encode_message(payload: EncodeRequest):
    """
    Encodes a text message into a semantic packet.
    If spaCy is installed, uses Farhan's real encoder; otherwise, uses a mock.
    Measures sizes, calculates compression, records encoding latency, and saves to SQLite.
    """
    start_time = time.perf_counter()
    
    if HAS_ENCODER:
        # Use Farhan's real encoder if available
        pkt_str, original_bytes, packet_bytes = semantic_encode(payload.message, mode=payload.mode)
        packet = json.loads(pkt_str)
    else:
        # Fallback to mock if spaCy is not installed
        packet = {
            "message": payload.message
        }
        original_bytes = len(payload.message.encode("utf-8"))
        packet_json = json.dumps(packet)
        packet_bytes = len(packet_json.encode("utf-8"))
    
    end_time = time.perf_counter()
    encoding_latency_ms = (end_time - start_time) * 1000
    
    if original_bytes > 0:
        compression_percentage = ((original_bytes - packet_bytes) / original_bytes) * 100
    else:
        compression_percentage = 0.0
        
    # Divy's Database Integration: Save the record to SQLite
    save_message(
        original_message=payload.message,
        semantic_packet=packet,
        original_bytes=original_bytes,
        packet_bytes=packet_bytes,
        compression_percentage=compression_percentage,
        encoding_latency_ms=encoding_latency_ms,
        processing_mode=payload.mode
    )
    
    return {
        "semantic_packet": packet,
        "benchmark": {
            "original_bytes": original_bytes,
            "packet_bytes": packet_bytes,
            "compression_percentage": compression_percentage,
            "encoding_latency_ms": encoding_latency_ms
        },
        "processing_mode": payload.mode
    }

@app.post("/decode", response_model=DecodeResponse)
def decode(request: DecodeRequest):
    """
    Decodes a semantic packet back into reconstructed text using Lovkush's decoder.
    Measures decoding latency and updates the database record.
    """
    start = time.perf_counter()
    
    # Call Lovkush's decode_packet function
    decoded_message = decode_packet(request.packet, mode=request.mode)
    
    decoding_latency_ms = (time.perf_counter() - start) * 1000

    # Divy's Database Integration: Update the message log with the decoded text and latency
    update_message_decoding(
        semantic_packet=request.packet,
        decoded_message=decoded_message,
        decoding_latency_ms=decoding_latency_ms
    )

    return DecodeResponse(
        decoded_message=decoded_message,
        decoding_latency_ms=decoding_latency_ms,
        mode=request.mode,
    )

@app.post("/validate")
def validate_reconstruction(payload: ValidateRequest):
    """
    Validates semantic similarity between original and reconstructed messages.
    Placeholder for future validation logic, updating database status.
    """
    validation_result = "review_required"
    
    # Divy's Database Integration: Update message validation result in SQLite
    update_message_validation(
        original=payload.original,
        reconstructed=payload.reconstructed,
        validation_result=validation_result
    )
    
    return {
        "status": validation_result,
        "issues": [
            "Validator integration pending"
        ]
    }
