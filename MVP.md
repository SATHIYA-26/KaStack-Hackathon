# MVP Status

Snapshot of `origin/main` as of this write-up. Documents what the minimum viable
product actually needs (per the hackathon brief) and which parts are done,
built-but-unwired, or missing.

## What "MVP" means here

The smallest thing that satisfies the brief: a running FastAPI service where a
message goes in to `/encode`, comes back out through `/decode`, gets checked by
`/validate`, and every step reports size/latency/compression numbers — for both
Normal and Low-Resource mode. Everything below is judged against that bar.

## Component status

| Component | File(s) | Status | Notes |
|---|---|---|---|
| Semantic extraction | `app/encoder.py` | Built | spaCy-based Normal mode + regex-based Low-Resource mode. Not yet imported by `main.py`. |
| `POST /encode` | `app/main.py` | **Placeholder** | Returns `{"message": payload.message}` as the "packet" — doesn't call `encoder.py` at all. Benchmark numbers it reports are meaningless until this is wired. |
| Packet → text reconstruction | `app/decoder.py` | Built | Deterministic template decoder, unit-tested against the dataset. |
| `POST /decode` | `app/main.py` | **Broken (dead code)** | Two `/decode` routes are registered; the first (a placeholder returning the static string `"Decoder integration pending"`) always wins the match. The real decoder is never reached by any request. |
| Meaning validation | `app/validator.py` | Built | Compares reconstructed-text semantics against the packet the encoder produced; returns `safe` / `review_required` / `failed`. Unit-tested. |
| `POST /validate` | `app/main.py` | **Not wired** | Still returns the hardcoded placeholder `{"status": "review_required", "issues": [...]}` regardless of input. `validator.py` exists but nothing calls it. |
| SQLite persistence | `database.py`, `test_database.py` | **Not integrated** | Schema matches the plan's `messages` table, but the files live at the repo root (not under `app/`) and `main.py` never imports or calls them — the `# TODO: Divy` comments in each route are still just comments. |
| `GET /history` | — | Missing | Not implemented anywhere yet. |
| Benchmarking | `app/main.py` | Partial | `/encode` computes bytes/compression/latency, but against the fake packet above. `/decode` reports latency only. `/validate` reports no benchmarking fields. |
| Dataset | `semantic_messages.csv` | Done | 60 messages, used to ground decoder/validator tests. |
| Tests | `tests/*.py` | Misleading | `test_api.py` still asserts the *placeholder* behavior (e.g. expects `"Decoder integration pending"` verbatim), so it currently passes for the wrong reason — it isn't testing real decode/validate behavior. `test_decoder.py` and `test_validator.py` test the real modules directly, bypassing the broken routes. |
| Dependencies | `requirements.txt` | Incomplete | Missing `spacy`, which `encoder.py` hard-requires — a fresh clone cannot import it without installing this manually first. |
| Architecture diagram | — | Missing | Required for submission. |
| Benchmark comparison report | — | Missing | Required for submission. |
| README (packet design, encoder/decoder logic) | `README.md` | Minimal | Still the original scaffold text; doesn't document the packet schema or module logic yet. |

## Bottom line

Every core module (encoder, decoder, validator, database) has been individually
built and works in isolation — but `main.py` doesn't actually call three of the
four (`encoder.py`, the real `decoder.py` path, `validator.py`), and none of them
are backed by the database. As it stands on `main`, hitting `/encode`,
`/decode`, or `/validate` does not exercise any of the real logic anyone has
built. The pipeline is not currently demoable end-to-end.

## Critical path to a working demo (shortest path, in order)

1. **Fix `app/main.py`**: remove the duplicate `/decode` route (delete the
   placeholder, keep the one that calls `decode_packet`); replace `/encode`'s
   fake packet with a real call to `encoder.semantic_encode`; replace
   `/validate`'s hardcoded response with a real call to `validator.validate`.
2. **Add `spacy` to `requirements.txt`** so `encoder.py` is importable on a
   fresh install.
3. **Wire `database.py`** into the three routes (move it under `app/` for
   consistency, call `init_db()` on startup, insert a row per request) and add
   `GET /history`.
4. **Rewrite `tests/test_api.py`** to assert real decode/validate behavior
   instead of the placeholder strings, so a green test suite actually means
   something.
5. Only after (1)–(2) work end-to-end: write the architecture diagram and
   benchmark comparison report, since both depend on the real pipeline's
   actual numbers, not placeholder ones.

## Known limitation to flag during the demo (not a wiring issue)

`encoder.py`'s NLP extraction has real accuracy gaps independent of the wiring
above: it doesn't parse word-numbers ("three", "five"), and digits embedded in
location names ("Gate 2", "Desk 18") get misread as quantities — sometimes
swallowing the real quantity entirely. This directly affects the required
"time, location, and quantity" demo message category and is worth being upfront
about rather than being surprised by it live.
