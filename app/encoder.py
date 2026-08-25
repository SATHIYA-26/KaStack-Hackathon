import spacy
import re
import json

# Initialization
print("Loading local NLP model...")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_low_resource(text: str) -> dict:
    """
    PHASE 6: Low-Resource Mode. 
    Bypasses the spaCy NLP model entirely to save compute on low-power devices.
    Relies purely on fast Regex and keyword scanning.
    """
    text_lower = text.lower()
    semantics = {
        "intent": "", "person": "", "object": "", "quantity": None,
        "location": "", "date": "", "time": "",
        "negation": False, "urgency": False, "warning": False
    }

    # Strict Boolean Checks (Regex)
    semantics["negation"] = bool(re.search(r"\b(not|never|don't|cannot|stop|abort|no|cancel)\b", text_lower))
    semantics["urgency"] = bool(re.search(r"\b(urgent|asap|immediately|critical|quick)\b", text_lower))
    semantics["warning"] = bool(re.search(r"\b(warning|danger|alert|threat)\b", text_lower))

    # Keyword Scanning for Intents & Objects (No AI)
    common_intents = ["send", "deliver", "restart", "update", "cancel", "schedule"]
    for intent in common_intents:
        if intent in text_lower:
            semantics["intent"] = intent
            break
            
    # Regex for Quantity
    qty_match = re.search(r"\b(\d+)\b", text_lower)
    if qty_match:
        semantics["quantity"] = int(qty_match.group(1))

    # Keyword Scanning for Known Locations
    known_locations = ["chennai", "london", "data center", "office", "hq"]
    for loc in known_locations:
        if loc in text_lower:
            semantics["location"] = loc.title()
            break

    # Regex Date & Time parsing
    if "tomorrow" in text_lower: semantics["date"] = "2026-08-26"
    elif "today" in text_lower: semantics["date"] = "2026-08-25"

    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = time_match.group(2) or "00"
        if time_match.group(3) == "pm" and hour != 12: hour += 12
        elif time_match.group(3) == "am" and hour == 12: hour = 0
        semantics["time"] = f"{hour:02d}:{minute}"

    return semantics

def extract_normal(text: str) -> dict:
    """
    PHASE 6: Normal Mode. 
    Uses full spaCy part-of-speech tagging and Named Entity Recognition (NER).
    """
    doc = nlp(text)
    text_lower = text.lower()
    semantics = {
        "intent": "", "person": "", "object": "", "quantity": None,
        "location": "", "date": "", "time": "",
        "negation": False, "urgency": False, "warning": False
    }

    # Booleans
    semantics["negation"] = bool(re.search(r"\b(not|never|don't|cannot|stop|abort|no|cancel)\b", text_lower))
    semantics["urgency"] = bool(re.search(r"\b(urgent|asap|immediately|critical|quick)\b", text_lower))
    semantics["warning"] = bool(re.search(r"\b(warning|danger|alert|threat)\b", text_lower))

    # POS Tagging
    for token in doc:
        if token.pos_ == "VERB" and not semantics["intent"]:
            semantics["intent"] = token.lemma_.lower()
        if token.dep_ in ["dobj", "pobj"] and not semantics["object"]:
            if token.ent_type_ == "PERSON": semantics["person"] = token.text
            else: semantics["object"] = token.text

    # NER Extraction
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not semantics["person"]: semantics["person"] = ent.text
        elif ent.label_ in ["GPE", "LOC", "FAC"] and not semantics["location"]: semantics["location"] = ent.text
        elif ent.label_ in ["CARDINAL", "QUANTITY"] and not semantics["quantity"]:
            try: semantics["quantity"] = int(re.sub(r'[^\d]', '', ent.text))
            except ValueError: pass

    # Regex fallbacks
    if semantics["quantity"] is None:
        m = re.search(r"\b(\d+)\b", text_lower)
        if m: semantics["quantity"] = int(m.group(1))

    if "tomorrow" in text_lower: semantics["date"] = "2026-08-26"
    elif "today" in text_lower: semantics["date"] = "2026-08-25"

    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = time_match.group(2) or "00"
        if time_match.group(3) == "pm" and hour != 12: hour += 12
        elif time_match.group(3) == "am" and hour == 12: hour = 0
        semantics["time"] = f"{hour:02d}:{minute}"

    return semantics

def semantic_encode(text: str, mode: str = "normal") -> tuple:
    """
    Main encoder function. Routes to the correct extraction engine based on mode.
    """
    # PHASE 6 ROUTING
    if mode == "low_resource":
        semantics = extract_low_resource(text)
    else:
        semantics = extract_normal(text)

    short_packet = {
        "i": semantics["intent"], "p": semantics["person"], "o": semantics["object"],
        "q": semantics["quantity"], "l": semantics["location"], "d": semantics["date"],
        "t": semantics["time"], "n": semantics["negation"], "u": semantics["urgency"],
        "w": semantics["warning"]
    }

    cleaned_packet = {k: v for k, v in short_packet.items() if v}
    orig_size = len(text.encode('utf-8'))
    pkt_str = json.dumps(cleaned_packet, separators=(',', ':'))
    pack_size = len(pkt_str.encode('utf-8'))

    return pkt_str, orig_size, pack_size

if __name__ == "__main__":
    msg = "Warning: Do not restart the database server immediately."
    print("NORMAL MODE (AI)")
    p1, o1, pack1 = semantic_encode(msg, mode="normal")
    print(p1)
    
    print("\nLOW RESOURCE MODE (Regex Only)")
    p2, o2, pack2 = semantic_encode(msg, mode="low_resource")
    print(p2)