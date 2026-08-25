from pydantic import BaseModel, Field
from typing import Literal, Dict, Any

class EncodeRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The text message to encode")
    mode: Literal["normal", "low_resource"] = "normal"

class DecodeRequest(BaseModel):
    semantic_packet: Dict[str, Any] = Field(..., description="The semantic packet representation")

class ValidateRequest(BaseModel):
    original: str = Field(..., min_length=1, description="The original input message")
    reconstructed: str = Field(..., min_length=1, description="The reconstructed message received from the decoder")
