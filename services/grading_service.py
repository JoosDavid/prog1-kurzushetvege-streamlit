from services.utils import normalize_answer


def grade_quiz(questions, user_answers):

    score = 0
    results = []

    for idx, q in enumerate(questions):

        correct_answers = [normalize_answer(a) for a in q["answers"]]
        user = user_answers[idx]

        # normalize user input
        if isinstance(user, list):
            user_answers_clean = [normalize_answer(u) for u in user]
        else:
            user_answers_clean = [normalize_answer(user)]

        first_correct = (
            len(user_answers_clean) > 0 and
            len(correct_answers) > 0 and
            user_answers_clean[0] == correct_answers[0]
        )

        all_correct = user_answers_clean == correct_answers

        if first_correct:
            score += 1

        if all_correct:
            score += 1

        results.append({
            "question": q["question"],
            "correct_answers": correct_answers,
            "user_answer": user_answers_clean,
            "first_correct": first_correct,
            "all_correct": all_correct
        })

    return {
        "score": score,
        "total": len(questions) * 2,  # because max is 2 per question
        "details": results
    }