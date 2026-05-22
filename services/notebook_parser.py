from services.utils import detect_answer_type
from pathlib import Path

def extract_output(code_cell):

    outputs = code_cell.get("outputs", [])

    for output in outputs:

        if output.output_type == "stream":

            text = output.get("text", "").strip()

            if text:
                return text

        elif output.output_type in [
            "execute_result",
            "display_data"
        ]:

            data = output.get("data", {})

            if "text/plain" in data:
                return data["text/plain"].strip()

    return ""


def parse_quiz(notebook):

    cells = notebook.cells

    # Ignore first 2 markdown cells
    cells = cells[2:]

    # Keep initialization code cell
    setup_cell = cells[0]

    # Remaining cells are quiz pairs
    quiz_cells = cells[1:]

    questions = []

    i = 0

    while i < len(quiz_cells) - 1:

        markdown_cell = quiz_cells[i]
        code_cell = quiz_cells[i + 1]

        if (
            markdown_cell.cell_type == "markdown"
            and code_cell.cell_type == "code"
        ):

            question = markdown_cell.source.strip()

            answer = extract_output(code_cell)

            answer_type = detect_answer_type(answer)

            questions.append({
                "question": question,
                "answer": answer,
                "type": answer_type
            })

        i += 2

    return questions