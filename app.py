import streamlit as st
import pandas as pd
from pathlib import Path
import json

from services.notebook_executor import execute_notebook
from services.notebook_parser import parse_quiz
from services.grading_service import grade_quiz
from services.data_loader import load_all_messages
from services.utils import hard_clean

from services.database import (
    save_result,
    fetch_results
)

st.session_state.clear()

def safe(x):
    try:
        return hard_clean(x)
    except:
        return ""


def debug_json_safe(obj):
    try:
        json.dumps(obj)
        return True
    except Exception as e:
        st.write("❌ INVALID OBJECT:", obj)
        st.write("❌ ERROR:", e)
        return False
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

for m in merged:
    m["sender_name"] = safe(m.get("sender_name"))
    m["content"] = safe(m.get("content"))
    m["content_clean"] = safe(m.get("content_clean"))

st.write("SESSION STATE BEFORE:", st.session_state)
# ---------------------------
# UI
# ---------------------------
st.title("Notebook Quiz App")

username = safe(st.text_input("Enter your name"))

# ---------------------------
# RUN NOTEBOOK ONLY WHEN REQUESTED
# ---------------------------
if st.button("Load Quiz"):

    notebook = execute_notebook(
        NOTEBOOK_PATH,
        exec_env={"merged": merged}  
    )

    questions = parse_quiz(notebook)

    st.write("QUESTIONS COUNT:", len(questions))

    if questions:
        st.write(questions[0])

    clean_questions = [
        {
            "question": safe(q["question"]),
            "answer": safe(q["answer"]),
            "type": q["type"]
        }
        for q in questions
    ]

    for q in clean_questions:
        debug_json_safe(q)
    
    st.session_state["questions"] = clean_questions

# ---------------------------
# QUIZ RENDERING
# ---------------------------
if "questions" in st.session_state:

    questions = st.session_state["questions"]
    user_answers = {}

    st.header("Quiz")

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

    if st.button("Submit Quiz"):

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

        st.success(
            f"Score: {results['score']} / {results['total']}"
        )

        st.header("Detailed Results")

        for item in results["details"]:

            st.markdown("---")
            st.write("Question:", item["question"])
            st.write("Your Answer:", item["user_answer"])
            st.write("Correct Answer:", item["correct_answer"])
            st.write("Correct:", item["correct"])

# ---------------------------
# LEADERBOARD
# ---------------------------
st.header("Leaderboard")

results = fetch_results()

for r in results:
    if not isinstance(r.username, str):
        st.write("BAD DB ROW:", r.username)

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