# CAPSTONE C3: Entity Resolution Agent (Domain C — UCC / Public Records)

> The integration exam. Build a ReAct agent that decides whether UCC filings under different name variations — "Acme Logistics LLC", "ACME LOGISTICS, L.L.C.", "Acme Logistics Inc." — refer to the same real-world company, then produces a merged risk profile with a calibrated confidence score.

## The Problem

Commercial data providers ingest UCC filings from 50 state registries. The same company appears under dozens of name variants (punctuation, suffixes, DBAs, typos). A false merge attaches another company's $1.2M lien to the wrong entity; a missed merge hides real risk. Your agent gathers evidence with five tools and makes the call — or refuses and flags for human review.

## Files

| File | Status | What It Is |
|------|--------|------------|
| `entity_tools.py` / `entity_tools.js` | Complete | 5 mock tools with structured errors (`is_error`, `error_category`, `is_retryable`) |
| `e2e_test.py` | Complete | Tool smoke tests — run BEFORE building the agent |
| `entity_agent.py` / `entity_agent.js` | **TODO** | The ReAct loop (system prompt, schemas, handlers provided) |

## The Five Tools

1. `search_filings_by_name` — fuzzy candidate search (Acme has 3 variants across DE/NY)
2. `fuzzy_match_score` — exact / normalized / token-sort scores + recommendation
3. `get_filing_details` — secured parties, collateral, lien amounts
4. `get_business_registry_data` — official SOS cross-reference (the tiebreaker)
5. `merge_entity_profile` — the FINAL action; **rejects confidence < 0.5 as INSUFFICIENT_EVIDENCE**

Note the error convention: tools never raise — they return `{"is_error": true, "error_category": ..., "is_retryable": ...}` and the model reads it. Registry NOT_FOUND is a *signal* (lower your confidence), not a crash.

## The Decision Criteria (already in the system prompt)

- token_sort ≥ 0.90 + same state + same address → MERGE (high confidence)
- token_sort ≥ 0.80 + same state → LIKELY MERGE (verify with registry)
- token_sort ≥ 0.70 + different state → INVESTIGATE (check registry)
- below → DISTINCT ENTITY
- **Never force a merge — flag conflicts for human review**

The expected resolution for the test query: ACME LOGISTICS, L.L.C. (DE) and Acme Logistics Company (DE) merge; **Acme Logistics Inc. (NY) stays separate** (different state, different registry entity). If your agent merges all three, it failed the exam.

## Build Order

1. `python e2e_test.py` — all 5 tools green before any agent code
2. Implement `run_entity_agent(query)` in `entity_agent.py`:
   - `messages = [system, user]`, loop capped at **15 iterations** (resolution legitimately needs 8–12 tool calls)
   - `finish_reason == "tool_calls"` → append assistant message (with `tool_calls` re-serialized as dicts), dispatch each call through `HANDLERS` (guard `json.loads` of arguments — malformed args → `{}`), append `role:"tool"` results
   - `finish_reason == "stop"` → return the final text
   - Unknown tool name → `{"is_error": True, "error_category": "UNKNOWN_TOOL"}` as the result, never a crash
3. `python entity_agent.py` — watch the resolution trace

## Troubleshooting (from the course)

- **Agent finishes after 1-2 tool calls without resolving** → Mistral-7B taking shortcuts; the system prompt's numbered process helps, or swap `MODEL = "mixtral"`/`"llama3"` for stronger reasoning
- **Loops to 15 without resolving** → usually a missing tool-result append (the model can't see what it learned)
- **`merge_entity_profile` returns INSUFFICIENT_EVIDENCE** → working as designed; the agent must gather more evidence or report a no-merge

## Grading Yourself

- [ ] All e2e tool tests pass
- [ ] The agent calls ≥4 different tools during resolution
- [ ] DE entities merged, NY entity kept separate, with stated reasoning
- [ ] Confidence is calibrated (0.8–0.95 for the DE merge — not 1.0, registry didn't confirm "Acme Logistics Company")
- [ ] A second run with "BuildRight Construction" produces a sensible (different) resolution

## Going Further

Wire in your earlier labs: M16 guardrails in front, M19 tracing inside the loop, M18's judge scoring the resolution text, M21's FastAPI wrapper around the whole thing. That stack IS the production system.
