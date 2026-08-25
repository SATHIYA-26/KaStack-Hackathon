from pydantic import BaseModel, Field
from typing import Literal, Dict, Any

class EncodeRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The text message to encode")
    mode: Literal["normal", "low_resource"] = "normal"

class DecodeRequest(BaseModel):
    packet: Dict[str, Any] = Field(..., description="The semantic packet to decode")
    mode: str = Field(default="normal", pattern="^(normal|low_resource)$")

class DecodeResponse(BaseModel):
    decoded_message: str
    decoding_latency_ms: float
    mode: str

class ValidateRequest(BaseModel):
    original: str = Field(..., min_length=1, description="The original input message")
    reconstructed: str = Field(..., min_length=1, description="The reconstructed message received from the decoder")
