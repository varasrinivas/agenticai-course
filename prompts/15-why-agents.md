# Why Agents: The Business Case

## Both End Up in FastAPI — So What's the Difference?

3-Layer Model:
- Layer 1: Infrastructure (FastAPI + Docker) — SAME in both
- Layer 2: Capabilities (Tools + ML Model) — SAME in both  
- Layer 3: Intelligence (Claude reasoning) — NEW with agents

Decision Engine Comparison:
| Aspect | ML in FastAPI | Agent in FastAPI |
| Who decides what to query | YOUR hardcoded SQL | Claude reasons |
| Who handles name variations | YOUR ILIKE pattern | Claude discovers |
| Who formats response | YOUR template | Claude writes narrative |
| New question type | YOU build new endpoint | Claude handles it |
| Logic change | YOUR code + redeploy | System prompt update |

## 7 Benefits
1. Reasoning replaces hardcoded logic (name match 78% -> 94%)
2. Natural language in (5 engineers -> 50 analysts)
3. Explainability built in (regulatory compliance)
4. Follow-ups without new code (0 new endpoints)
5. Multi-source synthesis (automates 40-60% integration work)
6. Graceful incomplete data (eliminates false negatives)
7. ML model gets smarter context (model gives probability, agent gives story)

## When NOT to Use Agents
- Batch processing 1M records ($10K+ agent cost vs $0 script)
- Sub-100ms response required (agents take 3-15 seconds)
- Deterministic compliance checks (must be reproducible)
- Simple CRUD operations (no reasoning needed)
- Machine-consumed output (structured API better)

Decision rule: human reads output -> agent. Machine consumes output -> API.

## Cost: $0.015 agent report vs $25-50 human analyst report
