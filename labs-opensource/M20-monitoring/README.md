# M20 Lab: Monitoring

> Evaluation (M18) is a pre-deploy exam; monitoring is the heart-rate monitor after. You'll build the two pieces that need no infrastructure: a **z-score drift detector** and a **feedback collector** that turns thumbs-down into eval cases — closing the loop back to M18.

## Prerequisites

- M18 + M19 complete

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `drift_detector.py` / `.js` | Rolling-window z-score drift alerts | Statistical drift: quality, tokens/query, tool-call frequency |
| 2 | `feedback_collector.py` | Thumbs-down → eval-case pipeline | Closing the feedback loop, double trigger condition |

> The full Prometheus + Grafana stack (Counter/Histogram/Gauge metrics, `@track_agent_run` decorator, docker-compose, alert rules) is in the course HTML — it's a stretch goal here because it needs Docker. The statistical core you build below is what those dashboards visualize.

## Step 1: DriftDetector

Three rolling windows (quality score, tokens/query, tool-call frequency). Implement `check_drift(metric, window)`:
- Need ≥30 samples before judging (provided constant) — small samples scream false alarms
- Compare the LATEST value against the mean/stddev of the window EXCLUDING it: `z = (current - mean) / std`
- `|z| ≥ 2` → warning; `|z| ≥ 3` → critical; else no alert
- Guard `std == 0` (constant history → any change is technically infinite drift; treat as no alert unless the value actually differs)

The provided test harness feeds 60 samples of stable behavior, then simulates degradation (quality drops 0.85→0.55, tokens triple). **Expect a handful of WARNINGS during the stable phase** — a 2-sigma rule fires ~5% of the time by pure chance; that's the statistics, not a bug. The assertions check what actually matters: **zero CRITICALS while stable, criticals on both quality and tokens once degraded**. (This warning-noise-vs-critical-page distinction is exactly why alerting systems page on 3-sigma, not 2-sigma.)

## Step 2: FeedbackCollector

Implement:
- `record_feedback(record)`: append JSONL; on `thumb == "down"` increment the failure counter and `_maybe_trigger_eval()`
- `_maybe_trigger_eval()`: trigger only when BOTH conditions hold — ≥`eval_trigger_threshold` new failures AND ≥`eval_trigger_interval` since last trigger (failures alone would retrigger in a burst; time alone would fire on one bad day)
- `_ingest_failures_to_eval_set()`: convert thumbs-down records into M18-compatible eval cases (`{"input", "reference_response", "source": "production_feedback", ...}`)

The trigger in this lab just prints + writes the eval cases file (the course version shells out to pytest — adapt to your CI).

## Run It

```bash
python starter/drift_detector.py      # pure algorithm, no LLM/infra needed
python starter/feedback_collector.py  # simulates 25 feedback events
```

## Stretch Goals

- Stand up the real stack: `pip install prometheus-client`, add the Counter/Histogram/Gauge metrics + `@track_agent_run` from the course HTML, run Prometheus + Grafana via docker-compose
- Feed the M19 trace JSONL into the drift detector (tokens and latency are already there)
- Implement sampling: only judge-score 10% of production runs, but 100% of runs that errored
