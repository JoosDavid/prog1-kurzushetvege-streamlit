from services.utils import detect_answer_type, hard_clean

def extract_output(code_cell):
    outputs = code_cell.get("outputs", [])
    collected = []

    for output in outputs:

        if output.get("output_type") == "stream":
            text = output.get("text", "")
            if isinstance(text, list):
                text = "".join(text)
            if text:
                collected.append(text)

        elif output.get("output_type") in ["execute_result", "display_data"]:
            data = output.get("data", {})
            text = data.get("text/plain", "")
            if isinstance(text, list):
                text = "".join(text)
            if text:
                collected.append(text)

    return collected[-1].strip() if collected else ""


def parse_quiz(notebook):

    questions = []

    pending_question = None

    for cell in notebook.cells:

        # STEP 1: find markdown question
        if cell.cell_type == "markdown":

            text = hard_clean(cell.source).strip()

            if text:
                pending_question = text

        # STEP 2: find code answer AFTER markdown
        elif cell.cell_type == "code" and pending_question:

            answer = extract_output(cell)
            answer = hard_clean(answer)

            if answer:

                questions.append({
                    "question": pending_question,
                    "answer": answer,
                    "type": detect_answer_type(answer)
                })

            pending_question = None

    return questions