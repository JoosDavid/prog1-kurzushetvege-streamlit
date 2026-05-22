from pathlib import Path
import json


def load_json(path: Path):
    """Load a JSON file safely."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_messages(obj):
    """
    Extract message list from different possible JSON formats:
    - {"messages": [...]}
    - [...]
    """
    if isinstance(obj, dict):
        msgs = obj.get("messages", [])
        return msgs if isinstance(msgs, list) else []

    if isinstance(obj, list):
        return obj

    return []


def normalize_message(m: dict) -> dict:
    """
    Force a consistent schema so notebooks NEVER crash.
    """

    if not isinstance(m, dict):
        return None

    return {
        # core fields
        "sender_name": m.get("sender_name", "unknown"),
        "content": m.get("content", "") or m.get("text", ""),
        "content_clean": m.get("content_clean", "") or m.get("content", ""),

        # timestamps
        "timestamp_ms": m.get("timestamp_ms", 0),

        # flags (safe numeric conversion)
        "is_unsent": int(m.get("is_unsent", 0) or 0),

        # photos can be int, list, or missing → normalize to int count
        "photos": (
            len(m["photos"]) if isinstance(m.get("photos"), list)
            else int(m.get("photos", 0) or 0)
        ),

        # optional time breakdown (may not exist in data)
        "year": m.get("year"),
        "month": m.get("month"),
        "day": m.get("day"),
    }


def is_names_file(filename: str) -> bool:
    return "names" in filename.lower()


def load_all_messages(json_dir: Path):
    """
    Loads all message JSON files and returns:
    - merged_messages (clean normalized list[dict])
    - names_data (raw names file or None)
    """

    merged_messages = []
    names_data = None

    for file in sorted(json_dir.glob("*.json")):
        data = load_json(file)

        # handle names file separately
        if is_names_file(file.name):
            names_data = data
            continue

        messages = extract_messages(data)

        for m in messages:
            cleaned = normalize_message(m)
            if cleaned is not None:
                merged_messages.append(cleaned)

    return merged_messages, names_data