import nbformat
from nbclient import NotebookClient


def execute_notebook(notebook_path: str, exec_env: dict):
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # inject environment via first cell (safe + standard)
    inject_code = "\n".join(
        f"{k} = globals().get('{k}')"
        for k in exec_env.keys()
    )

    nb.cells.insert(0, nbformat.v4.new_code_cell(inject_code))

    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        allow_errors=False,
    )

    return client.execute()