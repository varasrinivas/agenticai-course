# M18 Lab: Evaluation & Testing — LLM-as-Judge

> Three eval levels: unit tests for tools (code), integration tests for the loop (code), and quality judgments (only another LLM can score "did it reason well?"). This lab builds level 3: a local Mistral judge with a golden dataset.

## Prerequisites

- M17 complete (you've already met Mistral-as-judge for hallucinations)

## Files

| File | Status | What It Is |
|------|--------|------------|
| `eval_dataset.json` | Complete | 3 golden cases (entity resolution domain) — one deliberately bad answer |
| `llm_judge.py` / `.js` | **TODOs** | The judge: scoring + dataset runner |

## The Judge Prompt (provided — read it carefully)

Four scored dimensions: reasoning quality, faithfulness, evidence sufficiency, confidence calibration — plus two **bias mitigations** baked into the prompt:
- *"Do NOT favor longer or shorter answers"* (length bias is the #1 LLM-judge failure)
- *"Base ALL scores on the criteria, not whether you agree with the decision"*

## What You Implement

### `run_judge(question, answer, context)`
1. Format the template, call Mistral with **`temperature=0`** (deterministic-ish judging; still expect ~0.05 variance — run 3× and average if you need precision)
2. Strip markdown fences (regex provided in the TODO) before `json.loads`
3. On parse failure or API error: return all-zeros with `judge_error: True` — **a broken judge must not silently pass cases**

### `evaluate_with_judge(test_cases, threshold=0.70)`
Run all cases; a case passes iff `not judge_error and overall >= threshold`. Print `[PASS]`/`[FAIL]` per case; return `{results, pass_rate, passed, total}`.

## The Golden Dataset

Case `good-merge` reasons from two pieces of evidence to a calibrated 0.92 confidence → should score ≥0.7. Case `hallucinated-merge` cites a registry record that ISN'T in its context and claims 0.99 confidence on one weak clue → faithfulness and calibration should tank it. Case `honest-uncertainty` refuses to merge on insufficient evidence → judges often under-score honest refusals; if yours does, that's a real lesson about judge bias, not a bug in your code.

## Run It

```bash
python starter/llm_judge.py
```

**Pass criteria:** `good-merge` passes, `hallucinated-merge` fails. (`honest-uncertainty` is genuinely contested — note what your judge does with it.)

## Stretch Goals

- Run each case 3× and report mean ± stddev per dimension — see the judge's variance for yourself
- Add 2 cases from YOUR M09 RAG lab answers and judge them
- Write deterministic pytest unit tests for the M16 `redact_pii` function (level 1 of the pyramid — no LLM needed; see the course HTML for parametrize patterns)
- Wire this into CI: the course HTML has the GitHub Actions workflow that starts Ollama in the runner
