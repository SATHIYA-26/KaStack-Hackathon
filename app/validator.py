"""Meaning validator (Phase 3): checks whether a reconstructed message still carries
the semantics of the original message it was decoded from.

Design note: rather than duplicating Phase 1's extraction logic to independently
re-parse the original text, this calls the real encoder (app.encoder.semantic_encode)
to get the original's ground-truth packet, then re-extracts semantics from the
reconstructed text against decoder.py's own template shape. Whatever the encoder
extracts is treated as ground truth -- this validates the decode round-trip, not
the encoder's NLP accuracy (that's Phase 1's concern).
"""

import json
import re

from app.encoder import semantic_encode
from app.vocab import REVERSE_INTENT_PHRASES

STATUS_SAFE = "safe"
STATUS_REVIEW_REQUIRED = "review_required"
STATUS_FAILED = "failed"

# Fields whose mismatch makes the message unsafe to rely on.
CRITICAL_FIELDS = ("i", "q", "l", "d", "t", "w", "n")
# Fields whose mismatch only warrants a second look.
OPTIONAL_FIELDS = ("p", "o")

_DATE_RE = re.compile(r"\bon\s+(\d{4}-\d{2}-\d{2})\b")
_TIME_RE = re.compile(r"\bat\s+(\d{1,2}:\d{2})\b")
_URGENCY_RE = re.compile(r"(?i)\s*this is urgent\.?")
_QUANTITY_RE = re.compile(r"\b(\d+)\b")
_DESTINATION_RE = re.compile(
    r"\bto\s+([A-Za-z0-9][\w\s]*?)(?:\s+in\s+([A-Za-z0-9][\w\s]*?))?\s*(?=\.|$)"
)


def _cut(text: str, match: re.Match) -> str:
    remainder = text[: match.start()] + text[match.end():]
    return re.sub(r"\s+", " ", remainder).strip()


def _extract_intent(tokens: list[str]) -> tuple[str | None, int]:
    if not tokens:
        return None, 0
    if tokens[0].rstrip(".,!?").lower() == "process":
        return None, 1

    if len(tokens) >= 2:
        two_word = " ".join(t.rstrip(".,!?") for t in tokens[:2]).lower()
        if two_word in REVERSE_INTENT_PHRASES:
            return REVERSE_INTENT_PHRASES[two_word], 2

    one_word = tokens[0].rstrip(".,!?").lower()
    return REVERSE_INTENT_PHRASES.get(one_word, one_word), 1


def _extract_reconstructed_semantics(reconstructed: str, original_packet: dict) -> dict:
    working = reconstructed.strip()
    semantics = {"w": False, "n": False, "u": False}

    if working.lower().startswith("warning:"):
        semantics["w"] = True
        working = working.split(":", 1)[1].strip()

    if working.lower().startswith("do not"):
        semantics["n"] = True
        working = working[len("do not"):].strip()

    urgency_match = _URGENCY_RE.search(working)
    if urgency_match:
        semantics["u"] = True
        working = _cut(working, urgency_match)

    date_match = _DATE_RE.search(working)
    if date_match:
        semantics["d"] = date_match.group(1)
        working = _cut(working, date_match)

    time_match = _TIME_RE.search(working)
    if time_match:
        semantics["t"] = time_match.group(1)
        working = _cut(working, time_match)

    dest_match = _DESTINATION_RE.search(working)
    if dest_match:
        first = dest_match.group(1).strip().rstrip(".,")
        second = dest_match.group(2).strip().rstrip(".,") if dest_match.group(2) else None
        if second:
            semantics["p"] = first
            semantics["l"] = second
        elif original_packet.get("l") and not original_packet.get("p"):
            semantics["l"] = first
        elif original_packet.get("p") and not original_packet.get("l"):
            semantics["p"] = first
        else:
            # Ambiguous with no packet context to disambiguate: try both.
            semantics["l"] = first
            semantics["p"] = first
        working = _cut(working, dest_match)

    qty_match = _QUANTITY_RE.search(working)
    if qty_match:
        semantics["q"] = int(qty_match.group(1))
        working = _cut(working, qty_match)

    tokens = working.rstrip(".").split()
    intent, consumed = _extract_intent(tokens)
    semantics["i"] = intent
    obj = " ".join(tokens[consumed:]).strip()
    semantics["o"] = obj or None

    return semantics


def _normalize(field: str, value):
    if field in ("w", "n", "u"):
        return bool(value)
    if value is None:
        return None
    if field == "o" and isinstance(value, str):
        # Tolerate simple pluralization differences (e.g. "package" vs "packages").
        return value.strip().lower().rstrip("s")
    if isinstance(value, str):
        return value.strip().lower()
    return value


def validate(original: str, reconstructed: str, mode: str = "normal") -> dict:
    packet_json, _, _ = semantic_encode(original, mode=mode)
    original_packet = json.loads(packet_json)

    reconstructed_semantics = _extract_reconstructed_semantics(reconstructed, original_packet)

    mismatches = []
    for field in CRITICAL_FIELDS:
        original_value = _normalize(field, original_packet.get(field))
        reconstructed_value = _normalize(field, reconstructed_semantics.get(field))
        if original_value != reconstructed_value:
            mismatches.append(
                {
                    "field": field,
                    "severity": "critical",
                    "original": original_packet.get(field),
                    "reconstructed": reconstructed_semantics.get(field),
                }
            )

    review_flags = []
    for field in OPTIONAL_FIELDS:
        original_value = _normalize(field, original_packet.get(field))
        reconstructed_value = _normalize(field, reconstructed_semantics.get(field))
        if original_value != reconstructed_value:
            review_flags.append(
                {
                    "field": field,
                    "severity": "optional",
                    "original": original_packet.get(field),
                    "reconstructed": reconstructed_semantics.get(field),
                }
            )

    if mismatches:
        status = STATUS_FAILED
    elif review_flags:
        status = STATUS_REVIEW_REQUIRED
    else:
        status = STATUS_SAFE

    return {
        "status": status,
        "mismatches": mismatches,
        "review_flags": review_flags,
        "original_packet": original_packet,
        "reconstructed_semantics": reconstructed_semantics,
    }
