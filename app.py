import streamlit as st
import pandas as pd
from pathlib import Path

from services.notebook_executor import execute_notebook
from services.notebook_parser import parse_quiz
from services.grading_service import grade_quiz
from services.data_loader import load_all_messages
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
# LOAD DATA ONCE (IMPORTANT)
# ---------------------------
@st.cache_data
def get_data():
    return load_all_messages(JSON_DIR)

merged, names = get_data()

@st.cache_data
def load_quiz():
    notebook = execute_notebook(
        NOTEBOOK_PATH,
        exec_env={"merged": merged}
    )
    return parse_quiz(notebook)

# ---------------------------
# UI
# ---------------------------
st.title("Notebook Quiz App")

username = safe(st.text_input("Enter your name"))

if "questions" not in st.session_state:
    st.session_state["questions"] = None

if st.button("Load Quiz"):

    if st.session_state["questions"] is None:
        st.session_state["questions"] = [
            {
                "question": safe(q["question"]),
                "answer": safe(q["answer"]),
                "type": q["type"]
            }
            for q in load_quiz()
        ]

# ---------------------------
# QUIZ RENDERING
# ---------------------------

questions = st.session_state.get("questions")

if questions:

    with st.form("quiz_form"):
        st.header("Quiz")

        user_answers = {}

        for idx, q in enumerate(questions):

            st.markdown(f"### Question {idx + 1}")
            st.markdown(safe(q["question"]))

            if q["type"] == "integer":

                user_answers[idx] = st.number_input(
                    f"Answer {idx}",
                    step=1,
                    key=f"q_{idx}"
                )

            elif q["type"] == "float":

                user_answers[idx] = st.number_input(
                    f"Answer {idx}",
                    key=f"q_{idx}"
                )

            elif q["type"] == "boolean":

                user_answers[idx] = st.selectbox(
                    f"Answer {idx}",
                    ["True", "False"],
                    key=f"q_{idx}"
                )

            else:

                user_answers[idx] = st.text_input(
                    f"Answer {idx}",
                    key=f"q_{idx}"
                )

        submitted = st.form_submit_button("Submit Quiz")

        if submitted:

            if not username:
                st.warning("Please enter your name.")
                st.stop()

            safe_answers = {
                k: safe(v)
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
            st.session_state["questions"] = None


if "results" in st.session_state:

    st.success(
        f"Score: {st.session_state['results']['score']} / {st.session_state['results']['total']}"
    )

    st.subheader("Detailed Results")

    df = pd.DataFrame(st.session_state["results"]["details"])

    cols = ["question", "user_answer", "correct_answer", "correct"]
    df = df.reindex(columns=cols)

    st.dataframe(df)

# ---------------------------
# LEADERBOARD
# ---------------------------
st.header("Leaderboard")

results = fetch_results()

if results:

    leaderboard = pd.DataFrame([
        {
            "Username": safe(r.username),
            "Score": r.score,
            "Total": r.total
        }
        for r in results
    ])

    st.dataframe(
        leaderboard.sort_values(by="Score", ascending=False)
    )