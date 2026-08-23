# Quick Reference Cards

Data file for `scripts/build-study-guide.py`. Each `## ` heading becomes one card;
`~~~` fences render in the monospace face, everything else as body text.

Keep the numbers here, not in the script — they go stale and a data file is
reviewable in a diff.

<!-- pricing-verified: 2026-08-23 -->

## The Tool Use Loop

Used in every module from M05 onward. Learn this shape once.

~~~
messages = [user question]
WHILE true:
  response = claude(messages, tools)
  IF stop_reason == "end_turn": RETURN response
  FOR each tool_use in response:
    result = EXECUTE tool
    APPEND tool_result to messages
~~~

Return every tool_result for one assistant turn in a SINGLE user message.
Splitting them across messages teaches Claude to stop calling tools in parallel.

## The 8 Design Patterns

~~~
1. Single-Turn      one tool, one call
2. ReAct            think -> act -> observe -> loop
3. Plan-Execute     decompose first, then run
4. Router           classify input, route to handler
5. Parallel Fan-Out same task x many inputs
6. Pipeline         sequential stages
7. Supervisor       coordinator + specialist workers
8. Autonomous+HITL  agent runs, human approves key decisions
~~~

Pattern 8 is the one that matters in production. An agent that can take an
irreversible action without a human gate is a defect, not a feature.

## The 3 Agent Approaches

~~~
Raw   (M15B)  ~250 lines   full control, you write every line
SDK   (M26)    ~40 lines   hooks + sessions, the SDK runs the loop
Spec  (M25)   ~100 lines   spec text; Claude Code generates the rest
~~~

These are rungs on one ladder, not competing choices. Write the raw loop once so
you know what the SDK is doing for you.

## Cost Cheat Sheet

Anthropic first-party API rates, US dollars per million tokens.

~~~
MODEL             CONTEXT   INPUT    OUTPUT
Claude Opus 5     1M        $5.00    $25.00
Claude Sonnet 5   1M        $3.00    $15.00
Claude Haiku 4.5  200K      $1.00     $5.00
~~~

Batch API: 50% discount, asynchronous, for anything not latency-sensitive.
Prompt caching: cache reads bill well below base input rate — verify a cache is
actually hitting by reading `usage.cache_read_input_tokens`, not by assuming.

Bedrock and Vertex are partner-operated and priced separately. Check the pricing
page before quoting any of these in front of a customer; the rates above were
verified on the date at the top of this file.

## The 3 Deployment Tiers

~~~
Tier 1  Docker + DuckDB           free, local, no cloud account
Tier 2  GCP Cloud Run + BigQuery  pay-per-use, auto-scale
Tier 3  AWS Lambda + API Gateway  serverless, event-driven
~~~

M22B walks all three with the same agent. The agent code does not change; only
the handler wrapper and the state store do.

## Guardrails That Actually Hold

~~~
DENY before the tool runs, never after
Allow-list the safe shapes; do not deny-list the dangerous ones
The agent may never approve its own irreversible action
Audit every call, with credentials redacted per-value
~~~

A hook that logs the DROP after it executed is a good post-mortem and a useless
guardrail. See M16, M17, and Capstone 8.
