# M20 Lab: Monitoring & Continuous Improvement

> You can't improve what you can't see. A production agent without monitoring is a mystery box — you need dashboards, alerts, and drift detection to keep it healthy.

In this lab you build a terminal-based monitoring dashboard for a UCC filing agent. You will create a metrics collector, an alert engine, a drift detector, and a live ASCII dashboard — all from scratch, no external monitoring libraries.

## Prerequisites

- Python 3.10+ or Node.js 18+
- No external dependencies required (stdlib only)

## Exercises

| Step | Time | File | What You Build | Key Concept |
|------|------|------|---------------|-------------|
| 1 | 10 min | `metrics_collector.py/.js` | Metrics collector with latency percentiles, token costs, tool stats | Percentile calculation, cost modeling |
| 2 | 10 min | `alert_engine.py/.js` | Alert engine with configurable rules and severity levels | Threshold-based alerting, rule evaluation |
| 3 | 10 min | `drift_detector.py/.js` | Drift detector comparing current metrics against baseline | Statistical drift, significance thresholds |
| 4 | 15 min | `dashboard.py/.js` | ASCII dashboard with traffic simulator | Terminal rendering, end-to-end integration |
| 5 | 10 min | Run & observe | Simulate normal then degraded traffic, see alerts fire | Operational awareness |

## Step 1: Build the Metrics Collector (10 min)

**File:** `starter/metrics_collector.py` (or `.js`)

You will:
1. Implement `record_request()` — stores duration, token counts, success/failure, and tools used
2. Implement `get_latency_percentiles()` — returns p50, p75, p90, p95, p99 using sorted-array index-based calculation
3. Implement `get_error_rate()` — failed requests / total requests
4. Implement `get_token_stats()` — total input/output tokens, average per request, cost estimate using Claude Sonnet pricing ($3/M input, $15/M output)
5. Implement `get_tool_stats()` — per-tool call count, failure count, average duration
6. Implement `get_throughput()` — requests per minute over a sliding window

**Run it:**
```bash
python starter/metrics_collector.py
# or
node starter/metrics_collector.js
```

**Checkpoint:** Self-test records 100 simulated requests and prints summary stats. Percentiles should increase monotonically (p50 < p75 < p90 < p95 < p99).

## Step 2: Build the Alert Engine (10 min)

**File:** `starter/alert_engine.py` (or `.js`)

You will:
1. Define `AlertRule` — name, condition function, severity, message template
2. Define `Alert` — triggered alert with timestamp and metric value
3. Implement `AlertEngine.add_rule()` — register alert rules
4. Implement `AlertEngine.evaluate()` — check all rules against current metrics, return triggered alerts
5. Add default rules: error rate >5% (critical), latency p95 >10s (warning), cost >$1/hr (warning), tool failure >10% (critical), stale (no requests for 5+ min, info)

**Run it:**
```bash
python starter/alert_engine.py
# or
node starter/alert_engine.js
```

**Checkpoint:** Self-test creates metrics that trigger at least 2 alerts. Each alert shows severity, rule name, and the metric value that triggered it.

## Step 3: Build the Drift Detector (10 min)

**File:** `starter/drift_detector.py` (or `.js`)

You will:
1. Implement `set_baseline()` — snapshot current metrics as the baseline
2. Implement `detect_drift()` — compare current metrics against baseline, flag changes >20%
3. Implement `simulate_drift()` — artificially degrade metrics to test detection
4. Return `DriftEvent` objects with metric name, baseline value, current value, change percentage, and significance flag

**Run it:**
```bash
python starter/drift_detector.py
# or
node starter/drift_detector.js
```

**Checkpoint:** Self-test sets a baseline, simulates drift, and detects at least 2 significant drift events (>20% change).

## Step 4: Build the Dashboard (15 min)

**File:** `starter/dashboard.py` (or `.js`)

You will:
1. Implement `generate_traffic()` — simulate realistic request metrics with configurable error rate and slow percentage
2. Wire together MetricsCollector + AlertEngine + DriftDetector
3. Implement `render()` — print an ASCII box-drawing dashboard showing:
   - Request count, error rate, uptime
   - Latency percentiles
   - Token cost breakdown
   - Per-tool statistics
   - Active alerts (or "No active alerts")
   - Drift events (or "No significant drift detected")
4. Run two rounds: 200 normal requests, then 50 degraded requests — render dashboard after each

**Run it:**
```bash
python starter/dashboard.py
# or
node starter/dashboard.js
```

**Checkpoint:** Two dashboard renders appear. The second shows alerts firing and drift detected compared to the first baseline.

## Verification

After completing all exercises, run the solution to see expected behavior:

```bash
# Python
python solution/dashboard.py

# Node.js
node solution/dashboard.js
```

Compare your output against `expected_output/dashboard_output.txt`.

## Key Takeaways

- **Percentiles beat averages** — p95 tells you what your worst 5% of users experience
- **Alerts need severity levels** — not every anomaly is critical; triage matters
- **Drift detection catches slow degradation** — a metric that creeps 2% per day won't trigger a threshold alert but will trigger drift detection after a week
- **Dashboards are the entry point** — when something goes wrong, the dashboard is the first thing you check
