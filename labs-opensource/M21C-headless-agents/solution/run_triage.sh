#!/usr/bin/env bash
# M21C Lab - cron wrapper (SOLUTION)
# ==================================
# Cron itself does nothing with output or exit codes. This wrapper is where the
# headless discipline lives: explicit PATH, an OUTER os-level timeout backstop,
# capture stdout, and route each exit code to a different action.
#
# Crontab entry (run at 02:00 daily):
#   0 2 * * *  deploy  /opt/agents/run_triage.sh >> /var/log/triage.log 2>&1
set -uo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin   # cron's PATH is minimal — be explicit

cd "$(dirname "$0")"
LOGFILE="${1:-sample.log}"

# Run the agent. The outer `timeout` is a backstop in case the in-process
# guard is wedged; --signal=KILL guarantees the process dies after 45s.
# `|| CODE=$?` keeps the script alive (set -e would abort on non-zero exit).
OUT="$(timeout --signal=KILL 45s python3 triage_agent.py --file "$LOGFILE")"
CODE=$?

# Route by the exit-code contract: 0 ok / 1 transient / 2 bad output / 3 review.
case "$CODE" in
  0) echo "$OUT" | jq -c . >> reports.jsonl
     echo "[wrapper] OK -> reports.jsonl" ;;
  3) echo "$OUT" >> review_queue.jsonl
     echo "[wrapper] NEEDS REVIEW -> review_queue.jsonl" ;;
  2) echo "[wrapper] BAD OUTPUT (code 2) -> escalating, NOT retrying"
     # e.g. mail -s "triage bad output" oncall@example.com <<< "$OUT"
     ;;
  124|137) echo "[wrapper] TIMEOUT (code $CODE) -> killed by backstop, will retry next run" ;;
  *) echo "[wrapper] transient failure (code $CODE) -> will retry next run" ;;
esac

# The wrapper itself always succeeds: cron should not treat routed failures as
# its own failure. The routing above already handled the outcome.
exit 0
