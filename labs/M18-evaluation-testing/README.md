# M18 Lab: Evaluation & Testing

> Track 5 — Guardrails & Safety | Prerequisites: M12, M15B, M16, M17 | Time: 60-75 min

You built a UCC research agent in M15B. You added guardrails in M16-M17. But how do you **know** it works correctly? How do you catch regressions when you change the prompt or tools? This lab builds an **evaluation harness** that scores your agent on a suite of test cases using three different metric types.

**Estimated time: 60-75 minutes** | **70% hands-on lab, 30% concept**

## What You'll Build

An evaluation harness for the UCC research agent with:
- **20 test cases** across 4 categories (filing search, entity resolution, risk analysis, edge cases)
- **3 scorer types**: task completion (binary/partial), fuzzy entity matching, Claude-as-judge
- **An eval runner** that processes all cases and generates a report
- **Regression comparison** to detect score changes between runs

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` (`ANTHROPIC_API_KEY=sk-ant-...`) — only needed for Claude-as-judge; mock mode works without it
- Completed M15B lab (we use its mock data)
- Install dependencies:
  ```bash
  pip install anthropic python-dotenv
  ```

## Project Structure

```
M18-evaluation-testing/
├── starter/
│   ├── eval_dataset.py     # Complete — 20 test cases with expected outputs
│   ├── task_scorer.py       # TODO — task completion scoring
│   ├── fuzzy_scorer.py      # TODO — fuzzy entity matching
│   ├── judge_scorer.py      # TODO — Claude-as-judge scoring
│   └── eval_runner.py       # TODO — eval runner + report generation
├── solution/
│   ├── eval_dataset.py      # Same as starter (complete)
│   ├── task_scorer.py       # Complete implementation
│   ├── fuzzy_scorer.py      # Complete implementation
│   ├── judge_scorer.py      # Complete implementation
│   ├── eval_runner.py       # Complete implementation
│   ├── task_scorer.js       # Node.js version
│   ├── fuzzy_scorer.js      # Node.js version
│   ├── judge_scorer.js      # Node.js version
│   └── eval_runner.js       # Node.js version
└── expected_output/
    └── eval_report.txt      # Sample eval report
```

## Lab Steps

### Step 1: Explore the Eval Dataset (10 min)

**File:** `starter/eval_dataset.py`

This file is **already complete** — 20 test cases organized into 4 categories. Run it to see what you're working with:

```bash
cd starter
python eval_dataset.py
```

You should see a summary of all 20 test cases with their categories, difficulties, and expected outputs.

Study the test case structure:
- `id`: Unique identifier (e.g., `FS-001`)
- `category`: One of `filing_search`, `entity_resolution`, `risk_analysis`, `edge_case`
- `query`: The user question the agent must answer
- `expected`: Dict with `expected_filings`, `expected_entity`, `expected_risk_level`, `key_facts`
- `difficulty`: `easy`, `medium`, or `hard`

**Checkpoint:** You understand the 4 categories and what each test case checks.

### Step 2: Build the Task Completion Scorer (10 min)

**File:** `starter/task_scorer.py`

Build a scorer that checks whether the agent found the correct filings:
1. `score_task_completion(response, expected)` — compare filing numbers found in the response against expected filings
2. Partial credit: finding 3 of 5 expected filings = 0.6
3. Track found, missed, and extra (unexpected) filings
4. Return structured result: `{"score": 0.0-1.0, "found": [...], "missed": [...], "extra": [...]}`

**Test:**
```bash
python task_scorer.py
```

**Checkpoint:** Self-test passes — correct scores for full match, partial match, and no match.

### Step 3: Build the Fuzzy Match Scorer (10 min)

**File:** `starter/fuzzy_scorer.py`

Build a scorer for entity name matching (no external libraries):
1. `score_entity_match(response_entity, expected_entity)` — fuzzy string comparison
2. Uses token overlap (Jaccard similarity) — no external dependencies needed
3. `score_entity_resolution(response, expected)` — extract and score entity matches
4. Return: `{"score": 0.0-1.0, "matches": [...], "details": str}`

**Test:**
```bash
python fuzzy_scorer.py
```

**Checkpoint:** "Acme Corp" matches "Acme Corporation" with high score; "Totally Different" scores low.

### Step 4: Build the Claude-as-Judge Scorer (15 min)

**File:** `starter/judge_scorer.py`

Build a scorer that uses a **separate** Claude call to evaluate response quality:
1. `score_with_judge(query, response, expected, mock_mode=True)` — send query + response + rubric to Claude
2. Rubric scores: accuracy (0-5), completeness (0-5), clarity (0-5)
3. Normalize to 0.0-1.0 overall score
4. **Mock mode**: Return predetermined scores for testing without API calls
5. **Live mode**: Actually call Claude with a judge prompt (separate from the agent's system prompt)

**Test:**
```bash
python judge_scorer.py
```

**Checkpoint:** Mock mode returns consistent scores; structure matches expected format.

### Step 5: Build the Eval Runner (15 min)

**File:** `starter/eval_runner.py`

Build the orchestrator that ties everything together:
1. `EvalRunner` class with `run_eval(cases, agent_fn, mock_mode=True)`
2. For each test case: call the agent function → score with all 3 scorers → collect results
3. `generate_report(results)` — produce a formatted summary with per-category breakdown
4. `save_results(results, filepath)` — serialize results to JSON for regression tracking
5. `compare_runs(current, previous)` — compare two saved runs and highlight regressions
6. Mock agent function that returns realistic predetermined responses

**Test:**
```bash
python eval_runner.py
```

**Checkpoint:** Full eval runs in mock mode, report prints with per-category scores.

### Step 6: Run Eval and Analyze Report (10 min)

Run the complete evaluation pipeline:

```bash
python eval_runner.py
```

Expected output format:
```
===============================================
  UCC Research Agent — Evaluation Report
===============================================
Run ID: eval-2024-...
Cases:  20  |  Pass: 17  |  Fail: 3
Overall Score: 0.82
...
```

**Analysis questions:**
1. Which category has the lowest scores? Why?
2. Which test cases failed? Are they edge cases or fundamental issues?
3. What would you change in the agent to improve scores?

## Verification

Run the solutions to see expected behavior:

```bash
# Python
python solution/eval_runner.py

# Node.js
node solution/eval_runner.js
```

Compare your output against `expected_output/eval_report.txt`.

## What You Built

1. **20-case eval dataset** with expected outputs across 4 categories
2. **Task completion scorer** with partial credit and filing-level tracking
3. **Fuzzy entity matcher** using token overlap (no external deps)
4. **Claude-as-judge scorer** with structured rubric and mock mode
5. **Eval runner** with report generation and regression comparison

## Key Takeaways

- **Eval datasets are living documents** — add cases as you find bugs
- **Multiple metric types** catch different failure modes: binary (did it work?), fuzzy (close enough?), LLM-judge (quality?)
- **Mock mode is essential** — you need to iterate on the harness without burning API credits
- **Regression tracking** prevents "fix one thing, break another" cycles
- **Claude-as-judge** is powerful but not free — use it for quality dimensions that are hard to score programmatically

## Next

- **M19**: Observability & Tracing — monitor your agent in production
- **M20**: Cost & Latency Optimization — make it fast and cheap
