from services.utils import detect_answer_type, hard_clean

def extract_output(code_cell):
    outputs = code_cell.get("outputs", [])
    collected = []

    for output in outputs:

        if output.get("output_type") == "stream":
            text = output.get("text", "")

        elif output.get("output_type") in ["execute_result", "display_data"]:
            text = output.get("data", {}).get("text/plain", "")

        else:
            continue

        if isinstance(text, list):
            text = "".join(str(t) for t in text)

        for line in str(text).splitlines():
            line = line.strip()
            if line:
                collected.append(line)

    return collected


def parse_quiz(notebook):

    questions = []
    pending_question = None

    for cell in notebook.cells:

        if cell.cell_type == "markdown":
            text = hard_clean(cell.source).strip()
            if text:
                pending_question = text

        elif cell.cell_type == "code" and pending_question:

            answers = extract_output(cell)
            answers = [hard_clean(a) for a in answers if a]

            if answers:

                questions.append({
                    "question": pending_question,
                    "answers": answers,  
                    "type": "multi" if len(answers) > 1 else "single"
                })

            pending_question = None

    return questions