from pathlib import Path
import json


# =========================================================
# PATH RESOLUTION (works in notebook + streamlit + script)
# =========================================================

def get_data_dir() -> Path:
    """
    Tries to find the JSON folder no matter where you run from.
    Works in:
    - Streamlit
    - Jupyter notebook (nbclient)
    - python script
    """

    cwd = Path().resolve()

    candidates = [
        cwd / "json",
        cwd / "data" / "json",
        cwd.parent / "json",
        cwd.parent / "data" / "json",
        cwd.parent.parent / "data" / "json",
    ]

    for c in candidates:
        if c.exists():
            return c

    raise FileNotFoundError(f"JSON folder not found from: {cwd}")


# =========================================================
# JSON LOADING
# =========================================================

def load_json(path: Path):
    """
    Always UTF-8 safe.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_messages(obj):
    """
    Supports multiple formats:
    - {"messages": [...]}
    - [...]
    """
    if isinstance(obj, dict):
        msgs = obj.get("messages", [])
        return msgs if isinstance(msgs, list) else []

    if isinstance(obj, list):
        return obj

    return []


# =========================================================
# SAFE TYPE HELPERS
# =========================================================

def safe_int(x):
    try:
        return int(x)
    except:
        return 0


def safe_photos(x):
    if isinstance(x, list):
        return len(x)
    return safe_int(x)


# =========================================================
# TEXT SAFETY (fixes JÃ¡nos → János)
# =========================================================

def fix_encoding(text: str) -> str:
    """
    Repairs common UTF-8 mojibake issues.
    """
    if not isinstance(text, str):
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except:
        return text


# =========================================================
# NORMALIZATION (CRITICAL FOR NOTEBOOK STABILITY)
# =========================================================

def normalize_message(m: dict) -> dict:
    if not isinstance(m, dict):
        return None

    sender = m.get("sender_name") or "unknown"

    content = m.get("content") or m.get("text") or ""
    content_clean = m.get("content_clean") or content

    return {
        # identity
        "sender_name": fix_encoding(sender),

        # text
        "content": fix_encoding(content),
        "content_clean": fix_encoding(content_clean),

        # time
        "timestamp_ms": safe_int(m.get("timestamp_ms")),

        # flags
        "is_unsent": safe_int(m.get("is_unsent")),

        # media
        "photos": safe_photos(m.get("photos")),

        # optional breakdown (may not exist)
        "year": m.get("year"),
        "month": m.get("month"),
        "day": m.get("day"),
    }


# =========================================================
# FILE TYPE DETECTION
# =========================================================

def is_names_file(filename: str) -> bool:
    return "names" in filename.lower()


# =========================================================
# MAIN LOADER
# =========================================================

def load_all_messages(json_dir: Path):
    merged = []
    names = None

    for file in sorted(json_dir.glob("*.json")):
        data = load_json(file)

        # names file skip
        if is_names_file(file.name):
            names = data
            continue

        messages = extract_messages(data)

        for m in messages:
            cleaned = normalize_message(m)
            if cleaned:
                merged.append(cleaned)

    return merged, names