from services.utils import normalize_answer


def grade_quiz(questions, user_answers):

    score = 0
    results = []

    for idx, question_data in enumerate(questions):

        question_text = question_data["question"]

        try:
            first_score_weight = int(question_text[-7])
        except:
            first_score_weight = 1  # fallback safety

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

        # first answer correctness
        first_correct = (
            submitted_answers[0] == correct_answers[0]
            if correct_answers else False
        )

        # order-independent full correctness
        all_correct = (
            sorted(submitted_answers) == sorted(correct_answers)
            if len(correct_answers) > 1 else False
        )

        question_score = 0

        # base score depends on hidden rule
        if first_correct:
            question_score += first_score_weight

        # bonus rule (unchanged requirement)
        if len(correct_answers) > 1 and all_correct:
            question_score += 1

        score += question_score

        results.append({
            "question": question_text,
            "correct_answers": correct_answers,
            "user_answer": submitted_answers,
            "first_correct": first_correct,
            "all_correct": all_correct,
            "score": question_score,
            "first_score_weight": first_score_weight
        })

    return {
        "score": score,
        "total": sum(
            # max possible score per question = weight + bonus (if multi-answer)
            (int(q["question"][-7]) if isinstance(q["question"], str) and len(q["question"]) >= 7 else 1)
            + (1 if len(q["answers"]) > 1 else 0)
            for q in questions
        ),
        "details": results
    }