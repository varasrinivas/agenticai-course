# M14 Lab: Multi-Agent Systems

> Four specialists beat one generalist: researcher → writer → editor → reviewer, orchestrated by a supervisor with structured handoff messages and a revision loop. All four "agents" are the same Mistral model with different system prompts — specialization is prompt-deep, and that's enough.

## Prerequisites

- M13 complete

## Exercises (one file: `content_pipeline.py` / `.js`)

Provided complete: `create_handoff()` (the message envelope: sender, receiver, task_id, type, payload, **original_goal**), the four `AGENT_PROMPTS`, `run_agent()` (one specialist invocation), and the test harness.

**You build `run_pipeline(topic, max_review_attempts=2)`** — the supervisor:

1. **Research**: `run_agent("researcher", ...)` → log a handoff researcher→writer
2. **Write**: pass the goal AND the research to the writer → handoff writer→editor
3. **Edit**: editor improves the draft → handoff editor→reviewer
4. **Review with retry loop**: reviewer returns JSON `{"score": N, "feedback": "...", "approved": bool}`.
   - Parse defensively (fallback: treat unparseable review as approved with score 80 — don't let a malformed review block shipping)
   - If rejected and attempts remain: send the article + feedback BACK to the editor for revision, then re-review
5. Print the message log timeline; return `{topic, article, review, message_log, stages_completed}`

## The Two Design Rules Being Taught

1. **Every handoff carries `original_goal`.** By stage 3 the editor has never seen the user's request — without the goal in every message, the pipeline drifts ("telephone game"). Look at how every `run_agent` call re-states `Original goal: ...`.
2. **The reviewer is the quality gate, the supervisor is the decider.** The reviewer scores; the SUPERVISOR decides to retry or ship. Agents don't control flow — the orchestrator does.

## Run It

```bash
python starter/content_pipeline.py
```

Expect 4-6 model calls (~1-3 min on CPU). The output shows each stage, the review score, and the full handoff timeline.

## Gotchas

- **Mistral's reviewer JSON is flaky** — fences, prose preambles, missing fields. The defensive parse (fallback to approved/80) is deliberate: a broken gate should fail OPEN here, since a human reads the article anyway. In M17 you'll meet gates that must fail CLOSED.
- **Pass the previous stage's OUTPUT, not the whole log.** Each agent gets exactly what it needs: goal + immediate input. Dumping the full message log into every prompt burns tokens and confuses small models.

## Stretch Goals

- Add a 5th agent: "fact-checker" between editor and reviewer
- Run researcher and a "counter-researcher" (opposing viewpoints) in parallel, have the writer synthesize both
- Track per-agent token usage to see which specialist is most expensive
