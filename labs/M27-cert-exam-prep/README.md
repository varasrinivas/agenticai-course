# M27 Lab: Certification Exam Prep

> "You don't rise to the level of your knowledge. You fall to the level of your practice."

## Overview

This lab provides structured practice for the **Claude Certified Architect -- Foundations** exam. You will work through anti-pattern identification, scenario-based architecture decisions, mock exams, and domain scoring to identify your strengths and weaknesses across all 5 certification domains.

## Prerequisites

- **ALL previous modules (M01-M26)** -- This lab assumes mastery of every concept in the course
- Python 3.10+ or Node.js 18+
- No API keys required -- all exercises run locally against mock data

## Certification Domains

| Domain | Name | Weight | Key Modules |
|--------|------|--------|-------------|
| 1 | Agentic Architecture | 25% | M12, M13, M14, M26 |
| 2 | Tool Design & MCP | 20% | M05, M06, M07 |
| 3 | Claude Code Configuration | 20% | M25, M26 |
| 4 | Prompt Engineering & Structured Output | 15% | M03, M04, M16, M17 |
| 5 | Context & Reliability | 20% | M08, M11, M18, M19 |

## Exercises

| Step | Time | File | What You Build | Key Concept |
|------|------|------|----------------|-------------|
| 1 | 15 min | `anti_pattern_quiz.py` | Interactive anti-pattern identifier | All 18 anti-patterns across 5 domains |
| 2 | 15 min | `scenario_builder.py` | Architecture decision tool for exam scenarios | 6 exam scenarios, component selection |
| 3 | 15 min | `exam_runner.py` | Mock exam runner loading JSON questions | Question presentation, answer validation |
| 4 | 15 min | `domain_scorer.py` | Domain-based scorer with weak area analysis | 5 cert domains, study recommendations |

**Total time: ~60 minutes**

## Quick Start

### Python

```bash
# Step 1: Anti-pattern quiz
cd starter
python anti_pattern_quiz.py

# Step 2: Scenario builder
python scenario_builder.py

# Step 3: Run a mock exam
python exam_runner.py ../mock_exams/exam_a.json

# Step 4: Score across domains
python domain_scorer.py
```

### Node.js

```bash
# Step 1: Anti-pattern quiz
cd starter
node anti_pattern_quiz.js

# Step 2: Scenario builder
node scenario_builder.js

# Step 3: Run a mock exam
node exam_runner.js ../mock_exams/exam_a.json

# Step 4: Score across domains
node domain_scorer.js
```

## Exercise Details

### Exercise 1: Anti-Pattern Quiz (15 min)

**File:** `starter/anti_pattern_quiz.py` or `starter/anti_pattern_quiz.js`

Build an interactive display of all 18 certification anti-patterns. For each anti-pattern, your code should:

1. Display the anti-pattern number, name, and domain
2. Show a problematic code snippet or scenario
3. Explain WHY it is wrong
4. Show the correct pattern
5. Map it to the relevant certification domain

**What to implement:**
- The `ANTI_PATTERNS` data structure (starter has 3 examples, you add the rest)
- The `display_anti_pattern()` function
- The `run_quiz()` function that iterates through all 18

### Exercise 2: Scenario Builder (15 min)

**File:** `starter/scenario_builder.py` or `starter/scenario_builder.js`

Build an architecture recommendation tool for the 6 exam scenarios. Given a scenario number, output:

1. Scenario description
2. Recommended components (agent type, tools, hooks)
3. Session strategy (single vs multi-session)
4. Escalation rules
5. Key anti-patterns to avoid

**What to implement:**
- The `SCENARIOS` data structure (starter has 2 examples, you add the rest)
- The `build_architecture()` function
- The `display_scenario()` function

### Exercise 3: Exam Runner (15 min)

**File:** `starter/exam_runner.py` or `starter/exam_runner.js`

Build a mock exam runner that:

1. Loads questions from a JSON file
2. Presents each question with options
3. Accepts answers (or auto-answers for demo mode)
4. Scores the exam
5. Shows explanations for each question

**What to implement:**
- The `load_exam()` function
- The `present_question()` function
- The `score_exam()` function
- The `show_results()` function

### Exercise 4: Domain Scorer (15 min)

**File:** `starter/domain_scorer.py` or `starter/domain_scorer.js`

Build a domain-based scoring system that:

1. Takes results from multiple mock exams
2. Calculates per-domain scores
3. Identifies weak domains
4. Recommends specific modules to review
5. Estimates exam readiness

**What to implement:**
- The `calculate_domain_scores()` function
- The `identify_weak_areas()` function
- The `generate_report()` function

## Mock Exams

Three mock exams are provided in `mock_exams/`:

| Exam | Scenarios | Primary Domains | Questions |
|------|-----------|----------------|-----------|
| Exam A | 1 (Customer Support) + 3 (Multi-Agent Research) | 1, 2, 5 | 10 |
| Exam B | 2 (Claude Code) + 5 (CI/CD) | 3, 4 | 10 |
| Exam C | 4 (Developer Productivity) + 6 (Structured Extraction) | 2, 4, 5 | 10 |

Each exam has a corresponding answer key in `mock_exams/answer_keys/`.

## Verifying Your Work

Compare your output against the files in `expected_output/`:

- `exam_a_results.txt` -- Expected output from running exam A
- `domain_score_report.txt` -- Expected output from the domain scorer

## Tips for the Certification Exam

1. **stop_reason is king** -- Always check `stop_reason` for loop termination, never parse text
2. **Hooks over prompts** -- Critical rules need deterministic enforcement via hooks, not probabilistic prompts
3. **Escalate on capability, not sentiment** -- Angry customers with simple requests do not need humans
4. **Tool count matters** -- Keep coordinators under 8-10 tools, distribute via subagents
5. **Stratify your metrics** -- Aggregate accuracy hides per-category failures
6. **Environment variables for secrets** -- Never hardcode credentials in config files
7. **Provenance on everything** -- Every finding needs source, confidence, timestamp, agent_id
8. **Scratchpad files survive compaction** -- Use disk-based state for critical information
