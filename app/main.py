import json
import time
from fastapi import FastAPI, HTTPException
from app.models import EncodeRequest, DecodeRequest, ValidateRequest
import time

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.decoder import decode_packet

app = FastAPI(
    title="Semantic Communication Backend",
    description="Backend API layer with benchmarking for the Semantic Communication System.",
    version="1.0.0"
)


class DecodeRequest(BaseModel):
    packet: dict
    mode: str = Field(default="normal", pattern="^(normal|low_resource)$")


class DecodeResponse(BaseModel):
    decoded_message: str
    decoding_latency_ms: float
    mode: str


@app.get("/")
def read_root():
    """
    Health check and service status endpoint.
    """
    return {
        "status": "running",
        "service": "semantic-communication"
    }

@app.post("/encode")
def encode_message(payload: EncodeRequest):
    """
    Encodes a text message into a semantic packet.
    Measures sizes, calculates compression, and records encoding latency.
    """
    # 1. Benchmarking: Start latency timer
    start_time = time.perf_counter()
    
    # 2. Encoder Placeholder: Farhan's future encoder integration point.
    # Currently uses a simple mock representation mapping original message.
    packet = {
        "message": payload.message
    }
    
    # 3. Benchmarking: Stop latency timer and compute elapsed time in milliseconds
    end_time = time.perf_counter()
    encoding_latency_ms = (end_time - start_time) * 1000
    
    # 4. Calculate original message bytes in UTF-8
    original_bytes = len(payload.message.encode("utf-8"))
    
    # 5. Calculate packet bytes from serialized JSON representation
    packet_json = json.dumps(packet)
    packet_bytes = len(packet_json.encode("utf-8"))
    
    # 6. Calculate compression percentage
    if original_bytes > 0:
        compression_percentage = ((original_bytes - packet_bytes) / original_bytes) * 100
    else:
        compression_percentage = 0.0
        
    # TODO: Divy - Save the encoded message, semantic packet, and benchmark stats to database here
    
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

@app.post("/decode")
def decode_packet(payload: DecodeRequest):
    """
    Decodes a semantic packet back into reconstructed text.
    Provides a placeholder for Lovkush's future decoder.
    """
    # 1. Benchmarking: Start latency timer
    start_time = time.perf_counter()
    
    # 2. Decoder Placeholder: Lovkush's future decoder integration point.
    # Currently returns a static mock message.
    reconstructed_message = "Decoder integration pending"
    
    # 3. Benchmarking: Stop latency timer and compute elapsed time in milliseconds
    end_time = time.perf_counter()
    decoding_latency_ms = (end_time - start_time) * 1000
    
    # TODO: Divy - Fetch or update decoding history in the database here
    
    return {
        "reconstructed_message": reconstructed_message,
        "decoding_latency_ms": decoding_latency_ms
    }

@app.post("/validate")
def validate_reconstruction(payload: ValidateRequest):
    """
    Validates semantic similarity between original and reconstructed messages.
    Placeholder for future validation logic (SentenceTransformers/LLM-based).
    """
    # TODO: Divy - Log validation status and issues in database here
    return {
        "status": "review_required",
        "issues": [
            "Validator integration pending"
        ]
    }

@app.post("/decode", response_model=DecodeResponse)
def decode(request: DecodeRequest):
    start = time.perf_counter()
    decoded_message = decode_packet(request.packet, mode=request.mode)
    decoding_latency_ms = (time.perf_counter() - start) * 1000

    return DecodeResponse(
        decoded_message=decoded_message,
        decoding_latency_ms=decoding_latency_ms,
        mode=request.mode,
    )
