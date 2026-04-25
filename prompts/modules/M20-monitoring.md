# M20: Monitoring & Continuous Improvement

**Track**: 6 — Observability | **Position**: 20 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M19
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-observability) / #22C55E

## Concepts
- Production monitoring dashboards: latency, token usage, success/failure rates
- Drift detection: when agent behavior changes over time (animated degradation)
- Alerting: what warrants a page vs a ticket vs a log
- Feedback loops: using production data to improve the agent
- A/B testing in production: canary deployments for agents

## Hands-On Lab
Build a monitoring dashboard for the UCC agent: request count, p50/p95 latency, token cost per request, error rate, tool failure rate. Add an alert when error rate exceeds 5%. Simulate drift by degrading a tool.

## Quiz Focus (5 questions)
1. Dashboards = alerting? (no — dashboards are visual, alerting is proactive notification)
2. What is drift detection? (identifying when agent behavior changes without code changes)
3. More metrics = better insight? (no — too many metrics cause alert fatigue, focus on key signals)
4. Drift = bug? (not always — could be data distribution change, seasonal patterns, or model update)
5. How does canary deployment work for agents? (route 5% of traffic to new version, compare metrics, promote or rollback)
