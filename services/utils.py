import re

def clean_text(value):
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    # fix mojibake (JÃ¡nos → János)
    try:
        value = value.encode("latin1").decode("utf-8")
    except:
        pass

    # remove control chars (IMPORTANT for Streamlit + JSON + React frontend)
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    return value.strip()


def detect_answer_type(value):
    value = clean_text(value)

    if value == "":
        return "text"

    try:
        int(value)
        return "integer"
    except:
        pass

    try:
        float(value)
        return "float"
    except:
        pass

    if value.lower() in ["true", "false"]:
        return "boolean"

    return "text"


def normalize_answer(value):
    return clean_text(value).lower()


def hard_clean(value):
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    # fix encoding issues
    try:
        value = value.encode("latin1").decode("utf-8")
    except:
        pass

    # remove ALL control chars (this is what prevents URIError)
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    # normalize weird whitespace
    value = value.replace("\ufeff", "").strip()

    return value