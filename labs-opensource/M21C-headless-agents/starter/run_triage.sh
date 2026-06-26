#!/usr/bin/env bash
# M21C Lab - cron wrapper (STARTER)
# =================================
# Cron does nothing with output or exit codes. THIS wrapper is where the
# headless discipline lives. Most of it is done; you wire the routing.
#
# Crontab entry (run at 02:00 daily):
#   0 2 * * *  deploy  /opt/agents/run_triage.sh >> /var/log/triage.log 2>&1
set -uo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin   # cron's PATH is minimal — be explicit

cd "$(dirname "$0")"
LOGFILE="${1:-sample.log}"

# OUTER os-level backstop: even a wedged agent dies after 45s (--signal=KILL).
# `|| CODE=$?` keeps the script alive so we can inspect the code below.
OUT="$(timeout --signal=KILL 45s python3 triage_agent.py --file "$LOGFILE")"
CODE=$?

# TODO: route by the exit-code contract. Fill in the case branches:
#   0        -> append "$OUT" (pretty via `jq -c .`) to reports.jsonl
#   3        -> append "$OUT" to review_queue.jsonl (a human looks at these)
#   2        -> bad output: log + escalate, but do NOT retry (it won't succeed)
#   124|137  -> timeout/killed: log "will retry next run"
#   *        -> other transient failure: log "will retry next run"
case "$CODE" in
  0) : ;;   # TODO
  3) : ;;   # TODO
  2) : ;;   # TODO
  124|137) : ;;   # TODO
  *) : ;;   # TODO
esac

exit 0   # the wrapper itself always succeeds; routing already handled the outcome
