from services.utils import normalize_answer


def grade_quiz(questions, user_answers):

    score = 0

    results = []

    for idx, question_data in enumerate(questions):

        correct_answer = normalize_answer(
            question_data["answer"]
        )

        user_answer = normalize_answer(
            user_answers[idx]
        )

        correct = user_answer == correct_answer

        if correct:
            score += 1

        results.append({
            "question": question_data["question"],
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "correct": correct
        })

    return {
        "score": score,
        "total": len(questions),
        "details": results
    }