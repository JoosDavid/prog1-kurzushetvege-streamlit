from services.utils import normalize_answer


def grade_quiz(questions, user_answers):

    score = 0
    results = []

    for idx, question_data in enumerate(questions):

        correct_answers = [
            normalize_answer(a)
            for a in question_data["answers"]
        ]

        submitted_answers = [
            normalize_answer(a)
            for a in user_answers[idx]
        ]

        if not submitted_answers:
            submitted_answers = [""]

        first_correct = (
            submitted_answers[0] == correct_answers[0]
            if correct_answers else False
        )

        # order-insensitive comparison (safer in quizzes)
        all_correct = (
            sorted(submitted_answers) == sorted(correct_answers)
            if len(correct_answers) > 1 else False
        )

        question_score = 0

        if first_correct:
            question_score += 1

        if len(correct_answers) > 1 and all_correct:
            question_score += 1

        score += question_score

        results.append({
            "question": question_data["question"],
            "correct_answers": correct_answers,
            "user_answer": submitted_answers,
            "first_correct": first_correct,
            "all_correct": all_correct,
            "score": question_score
        })

    return {
        "score": score,
        "total": sum(
            2 if len(q["answers"]) > 1 else 1
            for q in questions
        ),
        "details": results
    }