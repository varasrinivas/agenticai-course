"""
M21C Lab - Headless contract self-test (NO Ollama required)
===========================================================
Verifies the part of the lab that must be deterministic: the headless
contract. We stub out the model call and assert that, for each kind of model
output, the agent (a) prints exactly ONE JSON object to stdout and (b) exits
with the right code.

    0  clean / non-critical anomalies     -> success
    2  model returns junk (non-JSON)      -> bad output, escalate
    3  a critical anomaly is present      -> needs review

Run:  python test_contract.py     (exit 0 = all green)

Copy this file next to your starter/triage_agent.py to grade your own work.
"""

import io
import sys
import json
import types
import contextlib

import triage_agent as ta


def _fake_resp(content: str, prompt=50, completion=20):
    """Mimic the openai client's response object shape."""
    msg = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=msg)
    usage = types.SimpleNamespace(
        prompt_tokens=prompt, completion_tokens=completion,
        total_tokens=prompt + completion,
    )
    return types.SimpleNamespace(choices=[choice], usage=usage)


def run_with_model_output(model_text: str):
    """Drive ta.main() end to end with a stubbed model and piped stdin."""
    # Stub the network call so no Ollama is needed.
    ta.client.chat.completions.create = lambda **kw: _fake_resp(model_text)

    old_argv, old_stdin = sys.argv, sys.stdin
    sys.argv = ["triage_agent.py"]                  # read from stdin, default guards
    sys.stdin = io.StringIO("some log line\nanother line")
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = ta.main()
    finally:
        sys.argv, sys.stdin = old_argv, old_stdin

    printed = out.getvalue().strip()
    # Contract guarantee #1: stdout is exactly one JSON object.
    assert printed.count("\n") == 0, f"stdout must be ONE line, got: {printed!r}"
    envelope = json.loads(printed)                  # raises if stdout is not pure JSON
    return code, envelope


CASES = [
    ("clean",
     '{"anomalies": [], "clean": true}',
     ta.EXIT_OK),
    ("non-critical anomaly",
     '{"anomalies": [{"line": "disk 91%", "reason": "high disk", "severity": "high"}], "clean": false}',
     ta.EXIT_OK),
    ("critical -> needs review",
     '{"anomalies": [{"line": "pool exhausted", "reason": "db down", "severity": "critical"}], "clean": false}',
     ta.EXIT_NEEDS_REVIEW),
    ("model junk -> bad output",
     "Sure! Here are the anomalies I found: the disk looks full.",
     ta.EXIT_BAD_OUTPUT),
    ("fenced JSON is tolerated",
     '```json\n{"anomalies": [], "clean": true}\n```',
     ta.EXIT_OK),
]


def main() -> int:
    failures = 0
    for name, model_text, expected_code in CASES:
        code, env = run_with_model_output(model_text)
        ok = code == expected_code and isinstance(env, dict) and "meta" in env
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name:30s} exit={code} (expected {expected_code})")
        if not ok:
            failures += 1
            print(f"          envelope={env}")
    print()
    if failures:
        print(f"{failures} case(s) FAILED")
        return 1
    print("all contract cases green (no Ollama needed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
