import streamlit as st
import pandas as pd
from pathlib import Path

from services.notebook_executor import execute_notebook
from services.notebook_parser import parse_quiz
from services.grading_service import grade_quiz

from services.database import (
    save_result,
    fetch_results
)

PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = "data/notebooks/quiz.ipynb"

st.title("Notebook Quiz App")

username = st.text_input("Enter your name")

if st.button("Load Quiz"):

    notebook = execute_notebook(NOTEBOOK_PATH, project_root=PROJECT_ROOT)

    questions = parse_quiz(notebook)

    st.session_state["questions"] = questions

if "questions" in st.session_state:

    questions = st.session_state["questions"]

    user_answers = {}

    st.header("Quiz")

    for idx, q in enumerate(questions):

        st.markdown(f"### Question {idx + 1}")

        st.markdown(q["question"])

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

        results = grade_quiz(
            questions,
            user_answers
        )

        save_result(
            username,
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

            st.write(
                "Your Answer:",
                item["user_answer"]
            )

            st.write(
                "Correct Answer:",
                item["correct_answer"]
            )

            st.write(
                "Correct:",
                item["correct"]
            )

st.header("Leaderboard")

results = fetch_results()

if results:

    leaderboard = pd.DataFrame([
        {
            "Username": r.username,
            "Score": r.score,
            "Total": r.total
        }
        for r in results
    ])

    st.dataframe(
        leaderboard.sort_values(
            by="Score",
            ascending=False
        )
    )