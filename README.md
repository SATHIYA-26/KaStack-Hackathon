# Semantic Communication System

A prototype semantic communication system built for low-resource networks (slow, expensive, or unreliable networks).

This system:
1. Extracts semantic elements (meaning) from natural-language messages.
2. Encodes those elements into a highly compressed semantic packet.
3. Decodes the semantic packet back into natural-language format.
4. Validates that the meaning of the reconstructed message matches the original.
5. Benchmarks size, compression ratio, latency, and meaning safety.
6. Stores benchmark history in a local SQLite database.
7. Supports both Normal Mode and Low-Resource Mode.

## Tech Stack
- Python 3
- FastAPI
- Uvicorn
- SQLite3
