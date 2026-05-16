# CAPSTONE-7: Agent Evolution — Build the Same Agent Three Ways

**Difficulty**: ★★★★★ | **Time**: 6-8 hours across 3 sessions | **Position**: FINAL capstone

## Concept
ONE agent built THREE times. Same tools, same mock data, same output. Each iteration uses a more advanced approach. The student compares code size, dev time, flexibility, control, and debugging.

## 3 Scenario Options (student picks one)

### Scenario A: Healthcare Pre-Auth Decision Agent
Tools: lookup_clinical_criteria, verify_diagnosis_match, check_network_status, get_benefit_summary, generate_determination
Mock: 15 pre-auth requests, 5 procedures (CPT codes), 3 payers, HIPAA callouts

### Scenario B: B2B Order Exception Agent
Tools: get_order_details, track_shipment, check_contract_pricing, query_inventory, draft_notification
Mock: 10 POs, 3 exception types, carrier tracking, contract pricing

### Scenario C: UCC Filing Risk Analyzer (default)
Tools: search_filings, predict_delinquency, get_filing_details
Mock: 12 filings, 3 entities, 5 states + pickle ML model

## ITERATION 1: Raw API Loop (Session 1, ~3 hours)
Steps 1-7: Setup, tools as JSON Schema, while loop, guardrails inline, logging manual, multi-turn manual, deploy as FastAPI+Docker
Debugging: print() in loop, manual message inspection
Result: ~250 lines, full control

## ITERATION 2: Agent SDK + Claude Code (Session 2, ~2 hours)
Steps 8-13: CLAUDE.md via Claude Code, @agent.tool decorators, hooks (logging+blocking+PII), sessions+fork, slash commands, deploy
Debugging: hooks as probes, Anthropic Console Web UI (console.anthropic.com > Logs), Langfuse traces
Result: ~120 lines, same output

## ITERATION 3: Spec-Driven (Session 3, ~1 hour)
Steps 14-17: Write agent-spec.md (12 sections), one Claude Code command generates 15-20 files, review+iterate, deploy
Debugging: spec vs code comparison, test-driven, eval-driven
Result: ~100 lines of spec, ~300 generated, same output

## Comparison Table
| Metric | Raw | SDK | Spec |
| Lines YOU wrote | ~250 | ~120 | ~100 |
| Time | ~3 hours | ~2 hours | ~1 hour |
| Guardrails | Inline | Hooks | Generated hooks |
| Debugging | print() | Hooks+Console+Langfuse | Spec comparison+tests |
| New tool | Edit 3 files | One command | Update spec |
| Documentation | Separate | CLAUDE.md | Spec IS docs |

## Key Takeaway
Iteration 1 teaches WHAT. Iteration 2 teaches HOW efficiently. Iteration 3 teaches HOW production teams work. Skip 1 and you cannot debug 3. Skip 3 and you are 10x slower.

## Grading: Iteration 1 (25%) + Iteration 2 (25%) + Iteration 3 (25%) + Comparison (15%) + Reflection (10%)
