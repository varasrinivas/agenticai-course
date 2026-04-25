"""
M27 Lab — Exercise 4 SOLUTION: Domain Scorer
==============================================
Score exam results by domain, identify weak areas, and generate
study recommendations.
"""

import json
from pathlib import Path


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

# Simulated exam results for demo purposes
# In production, these would come from actual exam_runner results
SIMULATED_RESULTS = {
    "mock_exam_a": {
        # 9/10 correct — miss A3 (Domain 1)
        "wrong_ids": ["A3"],
    },
    "mock_exam_b": {
        # 10/10 correct
        "wrong_ids": [],
    },
    "mock_exam_c": {
        # 8/10 correct — miss C2 (Domain 2) and C9 (Domain 5)
        "wrong_ids": ["C2", "C9"],
    },
}


def load_exam_results(exam_dir: str) -> list:
    """Load all exam JSON files and simulate answers for scoring."""
    exam_dir_path = Path(exam_dir)
    results = []

    exam_files = sorted(exam_dir_path.glob("exam_*.json"))
    if not exam_files:
        raise FileNotFoundError(f"No exam files found in {exam_dir}")

    for exam_file in exam_files:
        # Skip answer key directory
        if "answer_keys" in str(exam_file):
            continue

        with open(exam_file, "r", encoding="utf-8") as f:
            exam = json.load(f)

        exam_id = exam["exam_id"]
        sim = SIMULATED_RESULTS.get(exam_id, {"wrong_ids": []})
        wrong_ids = set(sim["wrong_ids"])

        question_results = []
        for q in exam["questions"]:
            is_correct = q["id"] not in wrong_ids
            question_results.append({
                "id": q["id"],
                "domain": q["domain"],
                "domain_name": q["domain_name"],
                "difficulty": q["difficulty"],
                "is_correct": is_correct,
                "correct_answer": q["correct_answer"],
            })

        results.append({
            "exam_id": exam_id,
            "title": exam["title"],
            "questions": question_results,
        })

    return results


def calculate_domain_scores(results: list) -> dict:
    """Calculate per-domain scores from all exam results."""
    domain_scores = {}

    for exam_result in results:
        for q in exam_result["questions"]:
            domain = q["domain"]
            if domain not in domain_scores:
                domain_scores[domain] = {
                    "name": q["domain_name"],
                    "correct": 0,
                    "total": 0,
                    "weight": DOMAINS.get(domain, {}).get("weight", 0),
                    "modules": DOMAINS.get(domain, {}).get("modules", []),
                }
            domain_scores[domain]["total"] += 1
            if q["is_correct"]:
                domain_scores[domain]["correct"] += 1

    # Calculate percentages
    for domain in domain_scores:
        ds = domain_scores[domain]
        ds["percentage"] = (
            (ds["correct"] / ds["total"] * 100) if ds["total"] > 0 else 0
        )

    return domain_scores


def identify_weak_areas(domain_scores: dict, threshold: float = 80.0) -> list:
    """Identify domains scoring below the threshold."""
    weak_areas = []

    for domain_num in sorted(domain_scores.keys()):
        ds = domain_scores[domain_num]
        if ds["percentage"] < threshold:
            weak_areas.append({
                "domain": domain_num,
                "name": ds["name"],
                "percentage": ds["percentage"],
                "modules": ds["modules"],
            })

    return weak_areas


def generate_report(domain_scores: dict, weak_areas: list) -> str:
    """Generate a formatted certification readiness report."""
    lines = []

    # Calculate combined totals
    total_correct = sum(ds["correct"] for ds in domain_scores.values())
    total_questions = sum(ds["total"] for ds in domain_scores.values())
    overall_pct = (
        (total_correct / total_questions * 100) if total_questions > 0 else 0
    )

    # Estimate exam score (scale to 1000)
    estimated_score = int(overall_pct * 10)

    # Determine readiness
    if overall_pct >= 85:
        recommendation = "READY for certification exam"
    elif overall_pct >= 72:
        recommendation = "NEEDS REVIEW — close to passing, address weak areas"
    else:
        recommendation = "NOT READY — significant preparation needed"

    lines.append("=" * 40)
    lines.append("Certification Readiness Report")
    lines.append("=" * 40)
    lines.append(f"Combined Score: {total_correct}/{total_questions} "
                 f"({overall_pct:.0f}%)")
    lines.append(f"Estimated Exam Score: ~{estimated_score}/1000")
    lines.append("")

    lines.append("Domain Breakdown:")
    best_domain = None
    best_pct = -1
    worst_domain = None
    worst_pct = 101

    for domain_num in sorted(domain_scores.keys()):
        ds = domain_scores[domain_num]
        pct = ds["percentage"]
        check = "+" if pct >= 72 else "-"
        lines.append(
            f"  Domain {domain_num} — {ds['name']} ({ds['weight']}%):  "
            f"{pct:.0f}% {check}"
        )

        if pct > best_pct:
            best_pct = pct
            best_domain = (domain_num, ds["name"])
        if pct < worst_pct:
            worst_pct = pct
            worst_domain = (domain_num, ds["name"])

    lines.append("")
    lines.append(f"Recommendation: {recommendation}")

    if best_domain:
        lines.append(f"Strongest: Domain {best_domain[0]} ({best_domain[1]})")
    if worst_domain:
        modules_str = ", ".join(
            domain_scores[worst_domain[0]].get("modules", [])
        )
        lines.append(
            f"Weakest: Domain {worst_domain[0]} ({worst_domain[1]}) — "
            f"Review {modules_str}"
        )

    if weak_areas:
        lines.append("")
        lines.append("Study Plan for Weak Areas:")
        for wa in weak_areas:
            modules_str = ", ".join(wa["modules"])
            lines.append(
                f"  Domain {wa['domain']} ({wa['name']}): "
                f"{wa['percentage']:.0f}% — Review {modules_str}"
            )

    output = "\n".join(lines)
    print(output)
    return output


def main():
    exam_dir = str(Path(__file__).parent.parent / "mock_exams")
    print(f"Loading exams from: {exam_dir}")
    print("(Demo mode: using simulated answers)\n")

    results = load_exam_results(exam_dir)
    print(f"Loaded {len(results)} exam(s)\n")

    domain_scores = calculate_domain_scores(results)
    weak_areas = identify_weak_areas(domain_scores)
    generate_report(domain_scores, weak_areas)


if __name__ == "__main__":
    main()
