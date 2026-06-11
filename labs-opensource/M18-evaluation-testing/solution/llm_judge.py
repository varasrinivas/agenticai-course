"""
M18 Lab: LLM-as-Judge Evaluation Harness — SOLUTION
====================================================
Run: python llm_judge.py    (reads ../starter/eval_dataset.json)
"""

import json
import os
import re

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

DATASET = os.path.join(os.path.dirname(__file__), "..", "starter", "eval_dataset.json")

JUDGE_PROMPT_TEMPLATE = """You are an impartial evaluator assessing the quality of an \
AI entity resolution agent's response. Score each dimension from 0.0 to 1.0.

QUESTION: {question}

AGENT RESPONSE: {answer}

RETRIEVED CONTEXT (what the agent had access to):
{context}

EVALUATION CRITERIA:
1. Reasoning quality (0-1): Does the agent reason step-by-step from evidence to conclusion? \
Does it cite specific filings, scores, or registry data before deciding?
2. Faithfulness (0-1): Does the answer use ONLY facts present in the retrieved context? \
Score 0 if it invents any fact not in context.
3. Evidence sufficiency (0-1): Did the agent use at least two independent pieces of evidence \
before reaching its confidence score? One clue is not enough for a high-confidence merge.
4. Confidence calibration (0-1): Is the confidence score plausible given the evidence? \
Score 1 if confidence matches evidence strength, 0 if they contradict.

IMPORTANT:
- Do NOT favor longer or shorter answers — length does not equal quality.
- Base ALL scores on the criteria above, not on whether you agree with the final decision.
- Return ONLY valid JSON — no markdown, no explanation outside the JSON.

Return:
{{
  "reasoning_quality": 0.0,
  "faithfulness": 0.0,
  "evidence_sufficiency": 0.0,
  "confidence_calibration": 0.0,
  "overall": 0.0,
  "explanation": "one sentence explaining the overall score"
}}"""

ZERO_SCORES = {
    "reasoning_quality": 0, "faithfulness": 0,
    "evidence_sufficiency": 0, "confidence_calibration": 0,
    "overall": 0,
}


def run_judge(question: str, answer: str, context: list[str],
              model: str = "mistral") -> dict:
    """Score one (question, answer, context) triple with the local judge."""
    ctx_str = "\n".join(f"- {c}" for c in context)
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question, answer=answer, context=ctx_str
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,   # (mostly) deterministic judging
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or ""
        # Mistral sometimes wraps JSON in ```json ... ``` fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # A broken judge must NOT silently pass cases
        return {**ZERO_SCORES, "explanation": f"JSON parse error: {e}", "judge_error": True}
    except Exception as e:
        return {**ZERO_SCORES, "explanation": str(e), "judge_error": True}


def evaluate_with_judge(test_cases: list[dict], threshold: float = 0.70) -> dict:
    """Run the judge on all cases; report pass/fail per case."""
    results = []
    for tc in test_cases:
        scores = run_judge(tc["question"], tc["answer"], tc["context"])
        passed = (
            not scores.get("judge_error")
            and scores.get("overall", 0) >= threshold
        )
        results.append({
            "id": tc["id"],
            "scores": scores,
            "passed": passed,
            "overall": scores.get("overall", 0),
        })
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {tc['id']}: overall={scores.get('overall', 0):.2f} — "
              f"{scores.get('explanation', '')}")

    passed_count = sum(1 for r in results if r["passed"])
    return {
        "results": results,
        "pass_rate": passed_count / len(results) if results else 0,
        "passed": passed_count,
        "total": len(results),
    }


if __name__ == "__main__":
    with open(DATASET, encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    print(f"Loaded {len(cases)} eval cases\n")
    print("Running LLM-as-judge (3 judge calls, ~1 min on CPU)...")

    summary = evaluate_with_judge(cases, threshold=0.70)

    print(f"\nPass rate: {summary['passed']}/{summary['total']} "
          f"({summary['pass_rate'] * 100:.0f}%)")
    print("\nExpected: good-merge PASSES, hallucinated-merge FAILS.")
    print("honest-uncertainty is contested — judges often under-score honest")
    print("refusals. Whatever yours did, that's data about judge bias.")
