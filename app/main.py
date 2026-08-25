import time

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.decoder import decode_packet

app = FastAPI(title="Semantic Communication System")


class DecodeRequest(BaseModel):
    packet: dict
    mode: str = Field(default="normal", pattern="^(normal|low_resource)$")


class DecodeResponse(BaseModel):
    decoded_message: str
    decoding_latency_ms: float
    mode: str


@app.get("/")
def read_root():
    return {
        "status": "running",
        "service": "semantic-communication"
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
