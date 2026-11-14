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


if "questions" not in st.session_state:
    st.session_state["questions"] = None

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

@st.cache_data(show_spinner="A kvíz előkészítése, kérlek várj...")
def load_quiz():
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
st.title("Notebook Quiz App")

username = safe(st.text_input("Enter your name"))

if "questions" not in st.session_state:
    st.session_state["questions"] = None

if st.button("Load Quiz"):
    if st.session_state["questions"] is None:
        notebook_mtime = (
            NOTEBOOK_PATH.stat().st_mtime_ns
            if NOTEBOOK_PATH.exists()
            else 0
        )

        st.session_state["questions"] = [
            {
                "question": safe(q["question"]),
                "answers": q["answers"],
                "type": q["type"]
            }
            for q in load_quiz(
                str(NOTEBOOK_PATH),
                notebook_mtime,
                DATA_SIGNATURE,
                merged,
                yearly
            )
        ]

        st.session_state["quiz_submitted"] = False
        st.session_state["results"] = None

# ---------------------------
# QUIZ RENDERING
# ---------------------------

questions = st.session_state.get("questions")
quiz_submitted = st.session_state.get("quiz_submitted", False)

if questions and not quiz_submitted:

    with st.form("quiz_form"):
        st.header("Quiz")

        user_answers = {}

        for idx, q in enumerate(questions):
        
            st.markdown(f"### Question {idx + 1}")
            st.markdown(safe(q["question"]))

            answers = q["answers"]
            user_answers[idx] = []

            if len(answers) == 1:
                user_answers[idx] = [
                    st.text_input(
                        f"Answer {idx}",
                        key=f"q_{idx}"
                    )
                ]
            else:
                user_answers[idx] = []
                for j in range(len(answers)):
                    user_answers[idx].append(
                        st.text_input(
                            f"Answer {idx}.{j+1}",
                            key=f"q_{idx}_{j}"
                        )
                    )

        submitted = st.form_submit_button("Submit Quiz")

        if submitted:

            if not username:
                st.warning("Please enter your name.")
                st.stop()

            safe_answers = {
                k: [safe(x) for x in v]
                for k, v in user_answers.items()
            }

            results = grade_quiz(
                st.session_state["questions"],
                safe_answers
            )

            save_result(
                safe(username),
                results["score"],
                results["total"]
            )

            st.session_state["results"] = results
            st.session_state["quiz_submitted"] = True
            st.session_state["questions"] = None


if st.session_state.get("quiz_submitted"):

    st.success(
        f"Score: {st.session_state['results']['score']} / {st.session_state['results']['total']}"
    )

    st.subheader("Detailed Results")

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

    st.dataframe(df, use_container_width=True, height=400)

# ---------------------------
# LIVE LEADERBOARD
# ---------------------------


@st.fragment(run_every="3s")
def render_leaderboard():

    st.header("Leaderboard")

    results = fetch_results()

    if results:

        leaderboard = pd.DataFrame([
            {
                "Username": safe(r["username"]),
                "Score": r["score"],
                "Total": r["total"]
            }
            for r in results
        ])

        leaderboard = leaderboard.sort_values(
            by="Score",
            ascending=False
        )

        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No results yet.")


render_leaderboard()
