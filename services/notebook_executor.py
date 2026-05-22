import nbformat
from nbclient import NotebookClient
from pathlib import Path

def execute_notebook(notebook_path, project_root):
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # inject project root into notebook namespace
    nb.metadata["project_root"] = str(project_root)

    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        allow_errors=False
    )

    client.execute()

    return nb