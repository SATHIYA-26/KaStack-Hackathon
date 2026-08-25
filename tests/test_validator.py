"""Validator tests.

`validate()` treats whatever app.encoder.semantic_encode() extracts from the
original message as ground truth, then checks whether the reconstructed message
still carries that same packet's semantics. That means: (1) a correct decode of
ANY encoder output should always validate SAFE (an invariant, independent of the
encoder's own NLP accuracy -- that's Phase 1's concern, not this validator's), and
(2) a genuinely corrupted reconstruction should be flagged FAILED (critical field)
or REVIEW_REQUIRED (optional field only).
"""

import json

import pytest

from app.decoder import decode_packet
from app.encoder import semantic_encode
from app.validator import STATUS_FAILED, STATUS_REVIEW_REQUIRED, STATUS_SAFE, validate

DATASET_MESSAGES = [
    "Please bring the project notebook to the lab.",
    "Meet Riya outside Gate 2 at 4:30 PM today.",
    "Do not upload the customer file; send only the anonymized summary.",
    "Don't restart Server B until the database backup is complete.",
    "The kitchen smells like gas; leave the room and alert the building security desk.",
    "Deliver three vegetarian meals to Desk 18 by 1:15 PM.",
    "Cancel today's client call, but keep tomorrow's internal review unchanged.",
    "Order 24 masks in size M and 12 in size L; no size S masks are required.",
]


@pytest.mark.parametrize("message", DATASET_MESSAGES)
@pytest.mark.parametrize("mode", ["normal", "low_resource"])
def test_correct_decode_of_real_encoder_output_is_always_safe(message, mode):
    packet_json, _, _ = semantic_encode(message, mode=mode)
    packet = json.loads(packet_json)
    decoded = decode_packet(packet, mode=mode)

    result = validate(message, decoded, mode=mode)

    assert result["status"] == STATUS_SAFE, (
        f"{message!r} ({mode}): packet={packet} decoded={decoded!r} "
        f"status={result['status']} mismatches={result['mismatches']} "
        f"review={result['review_flags']}"
    )
    assert result["mismatches"] == []
    assert result["review_flags"] == []


@pytest.mark.parametrize(
    "label, original, reconstructed",
    [
        ("negation dropped", "Do not restart Server B.", "Restart Server B."),
        (
            "warning dropped",
            "Warning: gas leak detected, evacuate the building now.",
            "Gas leak detected, evacuate the building now.",
        ),
        ("quantity wrong", "Send 3 packages to Chennai.", "Send 5 packages to Chennai."),
    ],
)
def test_critical_field_mismatch_is_failed(label, original, reconstructed):
    result = validate(original, reconstructed)
    assert result["status"] == STATUS_FAILED, f"{label}: expected FAILED, got {result['status']}"
    assert result["mismatches"], f"{label}: expected at least one critical mismatch"


def test_validate_handles_sparse_extraction_without_crashing():
    result = validate("Can you handle that thing we discussed earlier?", "Process.")
    assert result["status"] in (STATUS_SAFE, STATUS_REVIEW_REQUIRED, STATUS_FAILED)


def test_validate_result_shape():
    result = validate("Call Meera.", "Call Meera.")
    assert set(result) == {
        "status",
        "mismatches",
        "review_flags",
        "original_packet",
        "reconstructed_semantics",
    }
