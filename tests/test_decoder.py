"""Decoder tests grounded in semantic_messages.csv (see /data/Implementation plan).

Packets here are hand-crafted to represent what the encoder *should* produce for
each source message, since encoder.py isn't built yet. They double as a reference
for encoder/decoder packet-schema agreement, covering the demo's 5 categories.
"""

import pytest

from app.decoder import decode_packet

CASES = [
    # -- simple action --
    (
        "SEM_001",
        "Please bring the project notebook to the lab.",
        {"i": "bring", "o": "project notebook", "l": "lab"},
        ["bring", "project notebook", "lab"],
    ),
    (
        "SEM_009",
        "Call Meera when the model training finishes.",
        {"i": "call", "p": "Meera"},
        ["call", "meera"],
    ),
    # -- time + location + quantity --
    (
        "SEM_002",
        "Meet Riya outside Gate 2 at 4:30 PM today.",
        {"i": "meet", "p": "Riya", "l": "Gate 2", "t": "16:30"},
        ["meet", "riya", "gate 2", "16:30"],
    ),
    (
        "SEM_018",
        "Deliver three vegetarian meals to Desk 18 by 1:15 PM.",
        {"i": "deliver", "q": 3, "o": "vegetarian meal", "l": "Desk 18", "t": "13:15"},
        ["deliver", "3", "vegetarian meal", "desk 18", "13:15"],
    ),
    (
        "SEM_021",
        "Reserve a table for five at Spice Garden for 8 PM on Saturday.",
        {"i": "reserve", "q": 5, "o": "table", "l": "Spice Garden", "t": "20:00"},
        ["reserve", "5", "table", "spice garden", "20:00"],
    ),
    # -- negation --
    (
        "SEM_004",
        "Do not upload the customer file; send only the anonymized summary.",
        {"i": "upload", "n": True, "o": "customer file"},
        ["do not", "upload", "customer file"],
    ),
    (
        "SEM_012",
        "Don't restart Server B until the database backup is complete.",
        {"i": "restart", "n": True, "o": "Server B"},
        ["do not", "restart", "server b"],
    ),
    (
        "SEM_040",
        "Bring the blue insulin pouch from the refrigerator to City Hospital before 6 PM; "
        "do not bring the red pouch.",
        {"i": "bring", "o": "blue insulin pouch", "l": "City Hospital", "t": "18:00", "n": True},
        ["do not", "bring", "blue insulin pouch", "city hospital", "18:00"],
    ),
    # -- ambiguous / incomplete --
    (
        "SEM_006",
        "The delivery should arrive sometime in the evening.",
        {"i": "deliver"},
        ["deliver"],
    ),
    (
        "SEM_024",
        "The package is needed soon.",
        {"i": "request", "o": "package", "u": True},
        ["request", "package", "urgent"],
    ),
    # -- safety-sensitive --
    (
        "SEM_007",
        "The kitchen smells like gas; leave the room and alert the building security desk.",
        {"i": "alert", "o": "building security desk", "w": True},
        ["warning", "alert", "building security desk"],
    ),
    (
        "SEM_031",
        "The person is unconscious; call the local emergency service and do not offer food or drink.",
        {"i": "call", "o": "local emergency service", "w": True},
        ["warning", "call", "local emergency service"],
    ),
    (
        "SEM_053",
        "The battery is swelling; stop using the device, move away from it, and alert the "
        "responsible safety team.",
        {"i": "stop", "o": "device", "w": True, "u": True},
        ["warning", "stop", "device", "urgent"],
    ),
]


@pytest.mark.parametrize("message_id, original, packet, required", CASES)
def test_decode_preserves_critical_meaning(message_id, original, packet, required):
    decoded = decode_packet(packet).lower()
    for token in required:
        assert token.lower() in decoded, (
            f"{message_id}: expected '{token}' in decoded output, got: {decoded!r} "
            f"(original: {original!r})"
        )


def test_decode_preserves_explicit_zero_quantity():
    decoded = decode_packet({"i": "order", "q": 0, "o": "size S mask"}).lower()
    assert "0" in decoded, f"expected zero quantity to be preserved, got: {decoded!r}"


def test_decode_handles_empty_packet():
    assert decode_packet({}) == "Process."


def test_decode_never_crashes_on_partial_packet():
    partial_packets = [
        {"i": "alert"},
        {"n": True},
        {"w": True, "u": True},
        {"q": 5},
    ]
    for packet in partial_packets:
        assert isinstance(decode_packet(packet), str)
