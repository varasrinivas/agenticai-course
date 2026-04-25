"""
M27 Lab — Exercise 3: Exam Runner
==================================
Load and run mock exams from JSON files. Present questions, accept
answers, score the exam, and show explanations.

YOUR TASK: Implement load_exam(), present_question(), score_exam(),
and show_results().
"""

import json
import sys
from pathlib import Path


def load_exam(filepath: str) -> dict:
    """Load a mock exam from a JSON file.

    TODO: Implement this function. It should:
    1. Read the JSON file
    2. Validate it has required fields (exam_id, questions, passing_score)
    3. Return the parsed exam dict
    4. Raise FileNotFoundError or ValueError on errors
    """
    pass  # YOUR CODE HERE


def present_question(question: dict, index: int, total: int) -> str:
    """Display a question and return the user's answer.

    TODO: Implement this function. It should:
    1. Print the question number, domain, and difficulty
    2. Print the question text
    3. Print all 4 options (A, B, C, D)
    4. Return the correct answer (auto-answer mode for demo)

    For the starter, use auto-answer mode: always return the correct
    answer to demonstrate the flow.
    """
    pass  # YOUR CODE HERE


def score_exam(questions: list, answers: dict) -> dict:
    """Score the exam and return results.

    TODO: Implement this function. It should:
    1. Compare answers to correct answers
    2. Calculate total score and percentage
    3. Calculate per-domain scores
    4. Return a results dict with all scoring data
    """
    pass  # YOUR CODE HERE


def show_results(exam: dict, results: dict) -> str:
    """Display exam results and return formatted output.

    TODO: Implement this function. It should:
    1. Print overall score and pass/fail status
    2. Print per-domain breakdown
    3. Print per-question results with explanations
    4. Return the formatted output string
    """
    pass  # YOUR CODE HERE


def main():
    """Run a mock exam from a JSON file."""
    if len(sys.argv) < 2:
        # Default to exam_a.json
        exam_dir = Path(__file__).parent.parent / "mock_exams"
        filepath = str(exam_dir / "exam_a.json")
    else:
        filepath = sys.argv[1]

    print(f"Loading exam from: {filepath}")
    print("(Auto-answer mode: demonstrating with correct answers)\n")

    # TODO: Load exam, run questions, score, show results
    print("Not yet implemented — complete the functions above!")


if __name__ == "__main__":
    main()
