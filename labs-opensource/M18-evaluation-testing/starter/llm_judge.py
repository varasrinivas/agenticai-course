"""
M18 Lab: LLM-as-Judge Evaluation Harness
=========================================
Score agent answers on 4 quality dimensions with a local Mistral judge.
Run: python llm_judge.py    (reads eval_dataset.json from this folder)
"""

import json
import os
import re

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

DATASET = os.path.join(os.path.dirname(__file__), "eval_dataset.json")

# Judge prompt — note the explicit BIAS MITIGATIONS (COMPLETE)
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
    """Score one (question, answer, context) triple with the local judge.

    TODO:
    1. ctx_str = "\\n".join(f"- {c}" for c in context)
    2. prompt = JUDGE_PROMPT_TEMPLATE.format(question=..., answer=..., context=ctx_str)
    3. Call the model with temperature=0, max_tokens=512
       ← temp 0 = (mostly) deterministic judging; still expect ~0.05 variance
    4. Strip markdown fences before parsing:
         raw = re.sub(r"^```(?:json)?\\s*", "", raw.strip())
         raw = re.sub(r"\\s*```$", "", raw)
    5. return json.loads(raw)
    6. On json.JSONDecodeError or any other exception:
       return {**ZERO_SCORES, "explanation": str(e), "judge_error": True}
       ← a broken judge must NOT silently pass cases
    """
    pass  # Remove this line when you add your code


def evaluate_with_judge(test_cases: list[dict], threshold: float = 0.70) -> dict:
    """Run the judge on all cases; report pass/fail per case.

    TODO:
    For each tc in test_cases:
      1. scores = run_judge(tc["question"], tc["answer"], tc["context"])
      2. passed = (not scores.get("judge_error")) and scores.get("overall", 0) >= threshold
      3. Append {"id": tc["id"], "scores": scores, "passed": passed,
                 "overall": scores.get("overall", 0)} to results
      4. Print f"  [{'PASS' if passed else 'FAIL'}] {tc['id']}: "
               f"overall={overall:.2f} — {explanation}"
    Return {"results": results,
            "pass_rate": passed_count / len(results),
            "passed": passed_count, "total": len(results)}
    """
    pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──
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
