---
description: Improve explanation quality across all existing modules using depth rules 1-14
argument-hint: [MODULE_ID or ALL e.g. M09, M07, ALL]
---

Improve the explanation quality of module(s): $ARGUMENTS

If $ARGUMENTS is "ALL", apply to every module in output/. Otherwise apply to the specified module.

Read `prompts/07-depth-rules.md` first — it contains all 14 rules.
Read `prompts/06-cert-tip-callouts.md` — check if this module needs cert tips inserted.

For EACH module, apply these fixes using str_replace (do NOT regenerate the file):

## PASS 1: Dense Sentences (Rule 8)
Scan every tech-def-box and explain paragraph. Find sentences with 3+ technical terms crammed together. Break them into conversational steps using "First... Second..." or "Here's what happens step by step:" or "In other words,".

## PASS 2: Land Analogies (Rule 9)
After every analogy-box, check if there's a concrete "what it actually looks like" paragraph. If missing, add one showing the actual data structure, API response, or code artifact the analogy describes. The learner should go from metaphor to "Oh, THAT'S what it looks like."

## PASS 3: Expand Thin Sections (Rule 10)
Find any section that introduces a major NEW concept in less than 3 paragraphs. Expand with:
  - Paragraph 1: What it IS in plain English
  - Paragraph 2: How it WORKS internally (one level deeper)
  - Paragraph 3: How it DIFFERS from what the learner already knows

## PASS 4: Conversational Code Annotations (Rule 11)
Find code annotation blocks that read like bullet points ("WHAT: ... WHY: ... GOTCHA: ..."). Rewrite them as flowing teacher-voice paragraphs:
  - "Let's start by..." / "The interesting part is..." / "Here's the dilemma..."
  - Keep the WHAT/WHY/GOTCHA information but wrap it in narrative
  - Add tension and payoff to the explanation

## PASS 5: Common Misconceptions (Rule 12)
For each module, identify the major NEW concept introduced. Add a "Common Misconceptions" callout-warning box with 3-5 wrong mental models and corrections. Place it after the concept's main explanation, before the code walkthrough.

Major concepts by module:
- M00: Agents (agents aren't sentient, not running 24/7, just LLM + tools + loop)
- M01: LLMs (not a database, not deterministic, not "understanding")
- M02: Tokens (not words, not characters, cost implications)
- M03: Prompts (not programming, system prompts are not infallible)
- M04: Structured output (tool_use guarantees structure not semantics)
- M05: Function calling (Claude doesn't execute tools, tools aren't plugins)
- M06: Multi-tool (more tools ≠ better, tool selection degrades above 5)
- M07: MCP (not an API framework, not a chatbot plugin, servers are subprocesses)
- M08: Conversation management (Claude has no memory between calls, context ≠ memory)
- M09: RAG (not fine-tuning, bigger chunks ≠ better, doesn't eliminate hallucinations)
- M10: Advanced RAG (hybrid search isn't always better, re-ranking adds latency)
- M11: Memory (three tiers aren't always needed, episodic memory has privacy implications)
- M12: ReAct (agents aren't autonomous, stop_reason not NL parsing, iteration caps aren't stops)
- M13: Planning (not every task needs decomposition, overly narrow = coverage gaps)
- M14: Multi-agent (more agents ≠ better, subagents don't inherit coordinator context)
- M15: Code interpreter (sandbox ≠ safe, output parsing can fail, not for production computation)
- M15B: Agent system (coordinator doesn't do the work, parallel ≠ always faster, mock data ≠ production)
- M16: Input guardrails (prompts are not guardrails, PII detection isn't perfect, rate limits aren't security)
- M17: Output guardrails (confidence scores aren't reliable, sentiment ≠ complexity, same-session review is biased)
- M18: Evaluation (aggregate metrics hide failures, passing tests ≠ production-ready, eval datasets need maintenance)
- M19: Tracing (logging ≠ tracing, don't log PII, traces aren't free)
- M20: Monitoring (dashboards aren't alerting, more metrics ≠ better insight, drift ≠ bug)
- M21: Deployment (localhost ≠ production, streaming matters for agents, cold starts affect UX)
- M22: Cost optimization (caching can serve stale data, cheaper model ≠ same quality, premature optimization)
- M22B: Deployment (Docker image ≠ secure by default, env vars aren't encrypted, Lambda has timeout limits)
- M25: Claude Code (CLAUDE.md isn't a prompt, commands ≠ skills, plan mode isn't always better)
- M26: Hooks (hooks aren't prompts, maxTurns isn't a stop mechanism, fork_session ≠ new conversation)
- M27: Cert prep (anti-patterns look correct at first glance, memorization ≠ understanding, one mock exam isn't enough)

## PASS 6: Cert Tips (from prompts/06-cert-tip-callouts.md)
Check if this module has cert tip callouts listed. If yes and they're not already inserted, add them at the specified locations using the gold #D4A843 callout HTML.

## PASS 7: Hands-On Lab Instructions (Rule 13)
Find the hands-on exercise / lab section. Check and fix:
- If missing "What You'll Build" header with time estimate → add it
- If missing environment setup block (copy-pasteable install command) → add it
- For EACH step, verify it has ALL of these. Add any that are missing:
  a. Step number and title
  b. What & Why explanation (2-3 sentences)
  c. Explicit file instruction ("Create a new file called X" or "Add to X after the imports")
  d. COMPLETE code block (not a snippet — the full file or function for this step)
  e. Run command (exactly what to type: `python loader.py` or `node index.js`)
  f. Expected output (in an output block — what the terminal should show)
  g. Checkpoint callout (green box: "✅ If you see [output], Step N is working")
  h. Troubleshooting (2-3 common errors with solutions)
- If steps reference previous steps without saying so → add explicit dependency ("This uses X from Step 1")
- If missing final "Verify Everything Works" section → add it with end-to-end command + expected output
- If step says "implement X" without providing code → provide the complete code

## PASS 8: Gap Coverage (from prompts/11-gap-coverage.md)
Read `prompts/11-gap-coverage.md` and add missing sections to these specific modules:
- M04: Add multi-modal section (vision + PDF input to agents) — 200 words
- M12: Add error handling & retry patterns section + extended thinking section — 300 words each
- M19: Add compliance & audit logging section + prompt versioning section — 200 words each
- M21: Add streaming deep-dive section + authentication & authorization section — 300 words each
- M22: Add prompt caching section + batch API section — 200 words each
- M20: Add agent versioning & rollback section — 200 words
For modules NOT in this list, skip this pass.

## PASS 9: Progress Bar Update
Update any reference to "of 24" or "of 27" or "of 28" modules to "of 30".

After ALL passes, report per module:
- Word count: before → after
- Sections modified (list them)
- Passes applied (which of 1-9)
- Cert tips inserted (count)
- Lab steps fixed (count of steps that were incomplete)
- Gap sections added (list them)
- Estimated reading time: before → after
