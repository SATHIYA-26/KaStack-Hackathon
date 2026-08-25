"""Reconstructs a natural-language message from a semantic packet (see Implementation plan)."""

from app.vocab import INTENT_PHRASES


def _intent_phrase(intent: str | None) -> str:
    if not intent:
        return "Process"
    return INTENT_PHRASES.get(intent.lower(), intent.capitalize())


def _pluralize(word: str, quantity) -> str:
    if quantity == 1 or word.endswith("s"):
        return word
    return f"{word}s"


def _object_clause(quantity, obj: str | None) -> str | None:
    if quantity and obj:
        return f"{quantity} {_pluralize(obj, quantity)}"
    if obj:
        return obj
    return None


def _destination_clause(person: str | None, location: str | None) -> str | None:
    if person and location:
        return f"to {person} in {location}"
    if person:
        return f"to {person}"
    if location:
        return f"to {location}"
    return None


def decode_packet(packet: dict, mode: str = "normal") -> str:
    # mode is accepted for API/contract symmetry with the encoder; reconstruction
    # is deterministic template-filling and does not vary by mode.
    parts = []
    if packet.get("n"):
        parts.append("Do not")
    parts.append(_intent_phrase(packet.get("i")))

    object_clause = _object_clause(packet.get("q"), packet.get("o"))
    if object_clause:
        parts.append(object_clause)

    destination_clause = _destination_clause(packet.get("p"), packet.get("l"))
    if destination_clause:
        parts.append(destination_clause)

    if packet.get("d"):
        parts.append(f"on {packet['d']}")
    if packet.get("t"):
        parts.append(f"at {packet['t']}")

    sentence = " ".join(parts).strip()
    if not sentence.endswith((".", "!", "?")):
        sentence += "."

    if packet.get("u"):
        sentence += " This is urgent."
    if packet.get("w"):
        sentence = f"Warning: {sentence}"

    return sentence
