"""
M21C Lab - Headless Log-Triage Agent (STARTER)
==============================================
Build a headless agent a cron job runs nightly: read raw log lines on stdin,
ask Mistral to flag anomalies, emit ONE JSON envelope on stdout, log to stderr
only, and exit with a meaningful code.

Fill in the TODOs. Verify the deterministic parts WITHOUT Ollama by copying
solution/test_contract.py next to this file and running:  python test_contract.py
Then do a real run:  cat sample.log | python triage_agent.py 2>/dev/null | jq .

Requires: pip install openai   (+ Ollama with `ollama pull mistral`)
"""

import sys
import json
import time
import signal
import argparse

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "mistral"

# ── Exit-code contract (COMPLETE) ───────────────────────────────────────────
EXIT_OK = 0            # success
EXIT_TRANSIENT = 1     # operational failure (Ollama down, timeout) -> retry later
EXIT_BAD_OUTPUT = 2    # non-JSON / failed schema -> escalate, no retry
EXIT_NEEDS_REVIEW = 3  # ran fine, but a critical anomaly needs a human


class BadOutput(Exception):
    """Model output did not match our schema. Maps to exit code 2."""


class NeedsReview(Exception):
    """Ran fine but found something a human must see. Maps to exit code 3."""


class GuardTripped(Exception):
    """A guardrail (timeout / token budget) fired. Maps to exit code 1."""


def log(msg: str) -> None:
    # TODO 1: print human-readable progress to STDERR (not stdout!).
    #   Why: stdout must stay pure JSON so a caller can json.loads() it.
    #   Hint: print(..., file=sys.stderr)
    raise NotImplementedError("TODO 1: log() must write to stderr")


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
    # GUARD 1 (COMPLETE): wall-clock timeout via SIGALRM (Unix only).
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

    # TODO 2: GUARD 3 - token budget. If usage.total_tokens > max_tokens,
    #   raise GuardTripped(...). (In a multi-step loop you'd check every turn.)

    raw = resp.choices[0].message.content.strip()
    # Strip a ``` fence if Mistral wrapped the JSON (it often does).
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    # TODO 3: parse + validate the model output.
    #   - json.loads(raw); on JSONDecodeError raise BadOutput(...)
    #   - require it's a dict with keys "anomalies" (a list) and "clean";
    #     otherwise raise BadOutput(...)
    #   Assign the parsed dict to `report`.
    report = None  # replace me

    report["tokens"] = {
        "prompt": usage.prompt_tokens,
        "completion": usage.completion_tokens,
    }

    # TODO 4: business rule - if ANY anomaly has severity == "critical",
    #   raise NeedsReview("critical anomaly detected"). Attach the report to the
    #   exception (err.report = report) so the review queue keeps full context.

    return report


def read_logs(args) -> str:
    """Priority: --file, else stdin (so cron can pipe a log in). (COMPLETE)"""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not sys.stdin.isatty():
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

    # TODO 5: run analyze() inside try/except and map each outcome to an exit
    #   code + the fixed envelope shape:
    #     success            -> envelope["ok"]=True, envelope["data"]=report, code=EXIT_OK
    #     NeedsReview        -> envelope["data"]=err.report, error type "needs_review", code 3
    #     BadOutput          -> error type "bad_output", code 2
    #     GuardTripped       -> error type "guard_tripped", code 1
    #     any other Exception-> error type=type name, code 1 (transient)
    #   For each error set envelope["error"] = {"type": ..., "message": str(e)}
    raise NotImplementedError("TODO 5: wire analyze() to the envelope + exit codes")

    envelope["meta"] = {
        "exit_code": code,
        "latency_ms": int((time.time() - started) * 1000),
    }
    print(json.dumps(envelope))   # THE result -> stdout, one JSON line
    log(f"done in {envelope['meta']['latency_ms']}ms, exit={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())   # exit code IS the status API the cron wrapper reads
