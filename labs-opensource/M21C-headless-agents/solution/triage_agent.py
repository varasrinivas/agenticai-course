"""
M21C Lab - Headless Log-Triage Agent (SOLUTION)
===============================================
A headless agent a cron job runs every night: it reads raw log lines on
stdin, asks Mistral to flag anomalies, emits ONE JSON envelope on stdout,
logs to stderr only, and exits with a meaningful code.

The whole point: a program drives this, and a program consumes it. There is
no human in the loop, so the contract (stdout shape + exit code) is the API.

Run:
    cat sample.log | python triage_agent.py
    cat sample.log | python triage_agent.py 2>/dev/null | jq .
Requires: pip install openai   (+ Ollama running with `ollama pull mistral`)
"""

import sys
import json
import time
import signal
import argparse

from openai import OpenAI

# Ollama exposes an OpenAI-compatible API on localhost:11434
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "mistral"

# ── Exit-code contract ──────────────────────────────────────────────────────
EXIT_OK = 0            # success: valid result on stdout
EXIT_TRANSIENT = 1     # operational failure (Ollama down, timeout) -> retry later
EXIT_BAD_OUTPUT = 2    # model returned non-JSON / failed schema -> escalate, no retry
EXIT_NEEDS_REVIEW = 3  # ran fine, but a critical anomaly needs a human


class BadOutput(Exception):
    """Model output did not match our schema. Maps to exit code 2."""


class NeedsReview(Exception):
    """Ran fine but found something a human must see. Maps to exit code 3."""


class GuardTripped(Exception):
    """A guardrail (timeout / token budget) fired. Maps to exit code 1."""


def log(msg: str) -> None:
    # Human-readable progress -> stderr, so stdout stays pure JSON.
    print(f"[triage] {msg}", file=sys.stderr)


def _timeout_handler(signum, frame):
    raise GuardTripped("wall-clock timeout exceeded")


SYSTEM_PROMPT = (
    "You are a log-analysis agent. You are given raw log lines. "
    "Return ONLY a JSON object, no prose, in exactly this shape:\n"
    '{"anomalies": [{"line": <str>, "reason": <str>, '
    '"severity": "low|medium|high|critical"}], "clean": <bool>}\n'
    "List only genuinely suspicious lines (errors, security events, resource "
    "exhaustion). If nothing is wrong, return an empty anomalies list and "
    "clean=true. Use severity=critical only for outages or security breaches."
)


def analyze(logs: str, *, max_seconds: int, max_tokens: int) -> dict:
    """Call Mistral, validate the JSON, and enforce guardrails."""
    # GUARD 1: wall-clock timeout (Unix). SIGALRM fires after max_seconds.
    has_alarm = hasattr(signal, "SIGALRM")
    if has_alarm:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(max_seconds)
    try:
        log(f"analyzing {logs.count(chr(10)) + 1} log line(s)")
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": logs},
            ],
        )
    finally:
        if has_alarm:
            signal.alarm(0)  # always disarm the timer

    usage = resp.usage
    # GUARD 3: token budget (post-hoc here; in a multi-step loop, check each turn)
    if usage.total_tokens > max_tokens:
        raise GuardTripped(f"token budget {max_tokens} exceeded ({usage.total_tokens})")

    raw = resp.choices[0].message.content.strip()
    # Mistral sometimes wraps JSON in a ``` fence; strip it defensively.
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as e:
        raise BadOutput(f"model did not return valid JSON: {e}") from e

    # Schema validation — a small local model misses the shape more than you'd like.
    if not isinstance(report, dict) or "anomalies" not in report or "clean" not in report:
        raise BadOutput("JSON missing required keys 'anomalies'/'clean'")
    if not isinstance(report["anomalies"], list):
        raise BadOutput("'anomalies' must be a list")

    report["tokens"] = {
        "prompt": usage.prompt_tokens,
        "completion": usage.completion_tokens,
    }

    # Business rule: a critical anomaly is never auto-actioned -> needs a human.
    if any(a.get("severity") == "critical" for a in report["anomalies"]):
        # Attach the report so the review queue gets full context.
        err = NeedsReview("critical anomaly detected")
        err.report = report  # type: ignore[attr-defined]
        raise err

    return report


def read_logs(args) -> str:
    """Priority: --file, else stdin (so cron can pipe a log in)."""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not sys.stdin.isatty():            # data was piped in
        return sys.stdin.read().strip()
    raise SystemExit("no input: pipe logs on stdin or pass --file PATH")


def main() -> int:
    ap = argparse.ArgumentParser(description="Headless nightly log-triage agent")
    ap.add_argument("--file", help="log file to read; if omitted, read stdin")
    ap.add_argument("--max-seconds", type=int, default=30)
    ap.add_argument("--max-tokens", type=int, default=4000)
    args = ap.parse_args()

    started = time.time()
    envelope = {"ok": False, "data": None, "error": None, "meta": {}}
    code = EXIT_OK
    try:
        logs = read_logs(args)
        envelope["data"] = analyze(
            logs, max_seconds=args.max_seconds, max_tokens=args.max_tokens
        )
        envelope["ok"] = True
        code = EXIT_OK
    except NeedsReview as e:
        envelope["data"] = getattr(e, "report", None)
        envelope["error"] = {"type": "needs_review", "message": str(e)}
        code = EXIT_NEEDS_REVIEW
    except BadOutput as e:
        envelope["error"] = {"type": "bad_output", "message": str(e)}
        code = EXIT_BAD_OUTPUT
    except GuardTripped as e:
        envelope["error"] = {"type": "guard_tripped", "message": str(e)}
        code = EXIT_TRANSIENT
    except Exception as e:                       # connection refused, etc.
        envelope["error"] = {"type": type(e).__name__, "message": str(e)}
        code = EXIT_TRANSIENT

    envelope["meta"] = {
        "exit_code": code,
        "latency_ms": int((time.time() - started) * 1000),
    }
    # THE result -> stdout, as a single JSON line.
    print(json.dumps(envelope))
    log(f"done in {envelope['meta']['latency_ms']}ms, exit={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())   # exit code IS the status API the cron wrapper reads
