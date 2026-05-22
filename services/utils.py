def detect_answer_type(value):

    if value is None:
        return "text"

    value = str(value).strip()

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
    return str(value).strip().lower()