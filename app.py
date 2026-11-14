import streamlit as st
import pandas as pd
from pathlib import Path

from services.notebook_executor import execute_notebook
from services.notebook_parser import parse_quiz
from services.grading_service import grade_quiz
from services.data_loader import load_messages_by_year, merge_years
from services.utils import hard_clean

from services.database import (
    save_result,
    fetch_results
)

def safe(x):
    try:
        return hard_clean(x)
    except:
        return ""



# ---------------------------
# PATHS
# ---------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = PROJECT_ROOT / "data" / "notebooks" / "quiz.ipynb"
JSON_DIR = PROJECT_ROOT / "data" / "json"


# ---------------------------
# CACHE INVALIDATION HELPERS
# ---------------------------

def file_signature(path):
    path = Path(path)
    if not path.exists():
        return None
    stat = path.stat()
    return (
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size
    )


def directory_signature(directory):
    directory = Path(directory)
    return tuple(
        file_signature(file)
        for file in sorted(directory.glob("*.json"))
    )


# ---------------------------
# LOAD DATA
# ---------------------------

DATA_SIGNATURE = directory_signature(JSON_DIR)


@st.cache_data
def get_data(json_dir, data_signature):
    yearly, names = load_messages_by_year(Path(json_dir))
    merged = merge_years(yearly)
    return merged, yearly, names


merged, yearly, names = get_data(
    str(JSON_DIR),
    DATA_SIGNATURE
)


# ---------------------------
# LOAD QUIZ
# ---------------------------

NOTEBOOK_SIGNATURE = file_signature(NOTEBOOK_PATH)

@st.cache_data(show_spinner="A kvíz előkészítése, kérlek várj...")
def load_quiz(notebook_signature, data_signature):
    notebook = execute_notebook(
        NOTEBOOK_PATH,
        exec_env={
            "merged": merged,
            "yearly": yearly
        }
    )

    return [
        {
            "question": safe(q["question"]),
            "answers": q["answers"],
            "type": q["type"]
        }
        for q in parse_quiz(notebook)
    ]


# ---------------------------
# UI
# ---------------------------
st.title("Kurzushétvége Kvíz")

questions = load_quiz(
    NOTEBOOK_SIGNATURE,
    DATA_SIGNATURE
)

username = safe(st.text_input("Enter your name"))
if not username:
    st.info("Please enter your name to start the quiz.")
    st.stop()

# ---------------------------
# QUIZ RENDERING
# ---------------------------

quiz_submitted = st.session_state.get("quiz_submitted", False)

if questions and not quiz_submitted:

    with st.form("quiz_form"):
        st.header("Kvíz")

        user_answers = {}

        for idx, q in enumerate(questions):
        
            st.markdown(f"### Kérdés {idx + 1}")
            st.markdown(safe(q["question"]))

            answers = q["answers"]
            user_answers[idx] = []

            if len(answers) == 1:
                user_answers[idx] = [
                    st.text_input(
                        f"Válasz {idx+1}",
                        key=f"q_{idx}"
                    )
                ]
            else:
                user_answers[idx] = []
                for j in range(len(answers)):
                    user_answers[idx].append(
                        st.text_input(
                            f"Válasz {idx+1}.{j+1}",
                            key=f"q_{idx}_{j}"
                        )
                    )

        submitted = st.form_submit_button("Kvíz beadása")

        if submitted:

            if not username:
                st.warning("Kérlek, add meg a csapat nevét!")
                st.stop()

            safe_answers = {
                k: [safe(x) for x in v]
                for k, v in user_answers.items()
            }

            results = grade_quiz(
                questions,
                safe_answers
            )

            save_result(
                safe(username),
                results["score"],
                results["total"]
            )

            st.session_state["results"] = results
            st.session_state["quiz_submitted"] = True


if st.session_state.get("quiz_submitted"):

    st.success(
        f"Score: {st.session_state['results']['score']} / {st.session_state['results']['total']}"
    )

    st.subheader("Részletes Eredmények")

    raw = st.session_state["results"]["details"]

    flat = []

    for r in raw:
        flat.append({
            "question": r["question"],
            "user_answer": " | ".join(r["user_answer"]) if isinstance(r["user_answer"], list) else r["user_answer"],
            "correct_answers": " | ".join(r["correct_answers"]) if isinstance(r["correct_answers"], list) else r["correct_answers"],
            "first_correct": r.get("first_correct"),
            "all_correct": r.get("all_correct"),
        })

    df = pd.DataFrame(flat)

    cols = ["question", "user_answer", "correct_answers", "first_correct", "all_correct"]
    df = df.reindex(columns=cols)
    df.index = range(1, len(df) + 1)

    st.dataframe(df, use_container_width=True, height=400)

    if st.button("Új próbálkozás"):
        st.session_state["quiz_submitted"] = False
        st.session_state.pop("results", None)

        for key in list(st.session_state.keys()):
            if key.startswith("q_"):
                del st.session_state[key]

        st.rerun()

# ---------------------------
# LIVE LEADERBOARD
# ---------------------------


@st.fragment(run_every="3s")
def render_leaderboard():

    st.header("Ranglista")

    results = fetch_results()

    if results:

        leaderboard = pd.DataFrame([
            {
                "Csapatnév": safe(r["username"]),
                "Elért pont": r["score"],
                "Max pont": r["total"]
            }
            for r in results
        ])

        leaderboard = leaderboard.sort_values(
            by="Elért pont",
            ascending=False
        )

        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Még nincs eredmény.")


render_leaderboard()
