"""
M27 Lab — Exercise 3 SOLUTION: Exam Runner
============================================
Load and run mock exams from JSON files. Present questions, accept
answers (auto-answer mode for demo), score the exam, and show explanations.
"""

import json
import sys
from pathlib import Path


def load_exam(filepath: str) -> dict:
    """Load a mock exam from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Exam file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        exam = json.load(f)

    # Validate required fields
    required = ["exam_id", "questions", "passing_score"]
    for field in required:
        if field not in exam:
            raise ValueError(f"Exam file missing required field: {field}")

    if len(exam["questions"]) == 0:
        raise ValueError("Exam has no questions")

    return exam


def present_question(question: dict, index: int, total: int) -> str:
    """Display a question and return the answer (auto-answer mode)."""
    print(f"\n  Question {index + 1}/{total}")
    print(f"  ID: {question['id']} | Domain: {question['domain_name']} | "
          f"Difficulty: {question['difficulty']}")
    print(f"  {'-' * 50}")
    print(f"  {question['question']}")
    print()

    for letter in ["A", "B", "C", "D"]:
        print(f"    {letter}) {question['options'][letter]}")

    # Auto-answer mode: return the correct answer
    answer = question["correct_answer"]
    print(f"\n  > Auto-answer: {answer}")
    return answer


def present_question_wrong(question: dict, index: int, total: int) -> str:
    """Present a question and return a WRONG answer (for demo variety)."""
    print(f"\n  Question {index + 1}/{total}")
    print(f"  ID: {question['id']} | Domain: {question['domain_name']} | "
          f"Difficulty: {question['difficulty']}")
    print(f"  {'-' * 50}")
    print(f"  {question['question']}")
    print()

    for letter in ["A", "B", "C", "D"]:
        print(f"    {letter}) {question['options'][letter]}")

    # Pick a wrong answer (first option that isn't correct)
    correct = question["correct_answer"]
    wrong = [l for l in ["A", "B", "C", "D"] if l != correct][0]
    print(f"\n  > Auto-answer: {wrong} (intentionally wrong for demo)")
    return wrong


def score_exam(questions: list, answers: dict) -> dict:
    """Score the exam and return results."""
    total = len(questions)
    correct_count = 0
    per_question = []
    domain_scores = {}

    for q in questions:
        qid = q["id"]
        user_answer = answers.get(qid, "")
        is_correct = user_answer == q["correct_answer"]

        if is_correct:
            correct_count += 1

        per_question.append({
            "id": qid,
            "user_answer": user_answer,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
            "domain": q["domain"],
            "domain_name": q["domain_name"],
            "question_summary": q["question"][:60] + "...",
        })

        # Track per-domain scores
        domain = q["domain"]
        if domain not in domain_scores:
            domain_scores[domain] = {
                "name": q["domain_name"],
                "correct": 0,
                "total": 0,
            }
        domain_scores[domain]["total"] += 1
        if is_correct:
            domain_scores[domain]["correct"] += 1

    percentage = (correct_count / total * 100) if total > 0 else 0

    return {
        "total": total,
        "correct": correct_count,
        "percentage": percentage,
        "per_question": per_question,
        "domain_scores": domain_scores,
    }


def show_results(exam: dict, results: dict) -> str:
    """Display exam results and return formatted output."""
    lines = []
    passing = exam["passing_score"]
    passed = results["percentage"] >= passing

    lines.append("=" * 40)
    lines.append(f"{exam['title']} — Results")
    lines.append("=" * 40)
    lines.append(f"Score: {results['correct']}/{results['total']} "
                 f"({results['percentage']:.0f}%)")
    lines.append(f"Status: {'PASSED' if passed else 'FAILED'} "
                 f"(passing: {passing}%)")
    lines.append("")

    # Per-domain breakdown
    lines.append("Per-Domain Breakdown:")
    for domain_num in sorted(results["domain_scores"].keys()):
        ds = results["domain_scores"][domain_num]
        pct = (ds["correct"] / ds["total"] * 100) if ds["total"] > 0 else 0
        check = "+" if pct >= passing else "-"
        lines.append(
            f"  Domain {domain_num} ({ds['name']}):  "
            f"{ds['correct']}/{ds['total']} — {pct:.0f}% {check}"
        )
    lines.append("")

    # Per-question results
    lines.append("Questions:")
    for pq in results["per_question"]:
        mark = "+" if pq["is_correct"] else "X"
        lines.append(
            f"  {pq['id']}: {mark} ({pq['user_answer']}) — "
            f"{pq['question_summary']}"
        )
    lines.append("")

    # Weak areas
    weak_domains = []
    for domain_num, ds in results["domain_scores"].items():
        pct = (ds["correct"] / ds["total"] * 100) if ds["total"] > 0 else 0
        if pct < 80:
            weak_domains.append(f"Domain {domain_num}")

    if weak_domains:
        lines.append(f"Weak Areas: {', '.join(weak_domains)} — Review related modules")
    else:
        lines.append("Weak Areas: None — all domains above 80%")

    output = "\n".join(lines)
    print(output)
    return output


def run_exam(filepath: str, wrong_indices: list = None) -> dict:
    """Run a full mock exam and return results."""
    exam = load_exam(filepath)
    questions = exam["questions"]
    answers = {}

    print(f"\n{'=' * 56}")
    print(f"  {exam['title']}")
    print(f"  {exam['description']}")
    print(f"  Questions: {len(questions)} | Passing: {exam['passing_score']}% | "
          f"Time: {exam['time_limit_minutes']} min")
    print(f"{'=' * 56}")

    if wrong_indices is None:
        wrong_indices = []

    for i, question in enumerate(questions):
        if i in wrong_indices:
            answer = present_question_wrong(question, i, len(questions))
        else:
            answer = present_question(question, i, len(questions))
        answers[question["id"]] = answer

    print(f"\n{'=' * 56}")
    print("  Scoring...")
    print(f"{'=' * 56}\n")

    results = score_exam(questions, answers)
    show_results(exam, results)

    return {
        "exam_id": exam["exam_id"],
        "questions": questions,
        "answers": answers,
        "results": results,
    }


def main():
    """Run a mock exam from a JSON file."""
    if len(sys.argv) < 2:
        exam_dir = Path(__file__).parent.parent / "mock_exams"
        filepath = str(exam_dir / "exam_a.json")
    else:
        filepath = sys.argv[1]

    print(f"Loading exam from: {filepath}")
    print("(Auto-answer mode: demonstrating with correct answers, 1 wrong for demo)\n")

    # Get 9/10 correct (miss question index 2 for demo)
    run_exam(filepath, wrong_indices=[2])


if __name__ == "__main__":
    main()
