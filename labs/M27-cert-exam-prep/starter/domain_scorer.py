"""
M27 Lab — Exercise 4: Domain Scorer
====================================
Score exam results by domain, identify weak areas, and generate
study recommendations.

YOUR TASK: Implement calculate_domain_scores(), identify_weak_areas(),
and generate_report().
"""

import json
from pathlib import Path


# Domain definitions with weights and recommended modules
DOMAINS = {
    1: {
        "name": "Agentic Architecture",
        "weight": 25,
        "modules": ["M12", "M13", "M14", "M26"],
    },
    2: {
        "name": "Tool Design & MCP",
        "weight": 20,
        "modules": ["M05", "M06", "M07"],
    },
    3: {
        "name": "Claude Code Configuration",
        "weight": 20,
        "modules": ["M25", "M26"],
    },
    4: {
        "name": "Prompt Engineering & Structured Output",
        "weight": 15,
        "modules": ["M03", "M04", "M16", "M17"],
    },
    5: {
        "name": "Context & Reliability",
        "weight": 20,
        "modules": ["M08", "M11", "M18", "M19"],
    },
}


def load_exam_results(exam_dir: str) -> list:
    """Load all exam JSON files and simulate correct answers for scoring.

    TODO: Implement this function. It should:
    1. Find all exam_*.json files in the directory
    2. Load each exam's questions
    3. Simulate answers (for demo: get 9/10 on exam_a, 10/10 on exam_b,
       8/10 on exam_c — to show varied domain performance)
    4. Return a list of result dicts
    """
    pass  # YOUR CODE HERE


def calculate_domain_scores(results: list) -> dict:
    """Calculate per-domain scores from exam results.

    TODO: Implement this function. It should:
    1. Group questions by domain
    2. Calculate correct/total for each domain
    3. Calculate percentage for each domain
    4. Return a dict mapping domain number to score info
    """
    pass  # YOUR CODE HERE


def identify_weak_areas(domain_scores: dict, threshold: float = 80.0) -> list:
    """Identify domains scoring below the threshold.

    TODO: Implement this function. It should:
    1. Check each domain's percentage against the threshold
    2. Return a list of weak domains with recommended modules
    """
    pass  # YOUR CODE HERE


def generate_report(domain_scores: dict, weak_areas: list) -> str:
    """Generate a formatted certification readiness report.

    TODO: Implement this function. It should:
    1. Calculate combined score and estimated exam score
    2. Print per-domain breakdown with pass/fail indicators
    3. Print recommendation (READY / NEEDS REVIEW / NOT READY)
    4. Print strongest and weakest domains
    5. Return the formatted report string
    """
    pass  # YOUR CODE HERE


def main():
    exam_dir = str(Path(__file__).parent.parent / "mock_exams")
    print(f"Loading exams from: {exam_dir}")
    print("(Demo mode: using simulated answers)\n")

    # TODO: Load results, calculate scores, identify weak areas, generate report
    print("Not yet implemented — complete the functions above!")


if __name__ == "__main__":
    main()
