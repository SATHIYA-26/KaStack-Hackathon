# MVP Status

Snapshot of `origin/dev` (branch: `dev`, not yet merged into `main`). Documents
what the minimum viable product needs (per the hackathon brief) and the current
status of each part.

## What "MVP" means here

The smallest thing that satisfies the brief: a running FastAPI service where a
message goes in to `/encode`, comes back out through `/decode`, gets checked by
`/validate`, and every step reports size/latency/compression numbers — for both
Normal and Low-Resource mode, with results persisted to SQLite.

## Component status

| Component | File(s) | Status | Notes |
|---|---|---|---|
| Semantic extraction | `app/encoder.py` | Built and wired | spaCy-based Normal mode + regex-based Low-Resource mode. |
| `POST /encode` | `app/main.py` | Wired | Calls `encoder.semantic_encode` when spaCy is importable; falls back to a mock `{"message": ...}` packet otherwise (`HAS_ENCODER` check). Computes bytes/compression/latency and saves the row via `save_message`. |
| Packet → text reconstruction | `app/decoder.py` | Built and wired | Deterministic template decoder, unit-tested against the dataset. Single `/decode` route calls it directly. |
| `POST /decode` | `app/main.py` | Wired | Calls `decode_packet`, measures latency, updates the DB row via `update_message_decoding`. |
| Meaning validation | — | Not present | No validator module on this branch. |
| `POST /validate` | `app/main.py` | Placeholder | Returns a fixed `status: "review_required"` with `issues: ["Validator integration pending"]` regardless of input; logs that fixed result via `update_message_validation`. |
| SQLite persistence | `app/database.py` | Built and wired | `messages` table (schema matches the plan); `init_db()` runs on startup, and `/encode`, `/decode`, `/validate` all read/write through it. |
| `GET /history` | `app/main.py` | Built | Returns logged rows via `get_history(limit=...)`. |
| Benchmarking | `app/main.py` | Partial | `/encode` reports bytes, compression %, and latency against whichever packet it produced (real or fallback). `/decode` reports latency. `/validate` reports no benchmarking fields. |
| Dataset | `semantic_messages.csv` | Done | 60 messages. |
| Tests | `tests/test_api.py`, `tests/test_decoder.py` | Present | `test_api.py` checks real `/encode` and `/decode` behavior (accepts either the real or fallback packet shape); no test file targets `/validate`'s logic beyond payload validation, since there is no validation logic yet. |
| Dependencies | `requirements.txt` | fastapi, uvicorn, pydantic, httpx, pytest | `spacy` is not listed; `/encode`'s `HAS_ENCODER` try/except is what keeps the app running without it. |
| Architecture diagram | — | Not present | |
| Benchmark comparison report | — | Not present | |
| README (packet design, encoder/decoder logic) | `README.md` | Written | Documents the file structure, packet schema, DB schema, all four endpoints with example payloads, and setup/run instructions. |

## Bottom line

`/encode` → `/decode` → SQLite is wired end-to-end and demoable, in both modes.
`/validate` accepts input and logs a result, but the result itself is a fixed
placeholder rather than a computed comparison of the original and reconstructed
messages.
