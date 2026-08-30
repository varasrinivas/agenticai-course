"""Run the Claude-course lab solutions that call the Anthropic API.

Why this is separate from labs-opensource/harness/run_labs.py
------------------------------------------------------------
That harness discovers its work from the `$ python solution/x.py` lines the
Ollama course puts at the top of each expected_output block. This course's
samples are not that shape -- they are transcripts of an interactive agent
session -- so that discovery finds nothing here, and the Ollama harness has
never covered these labs. Work is discovered by scanning instead: solution
scripts that import anthropic and have a __main__ block.

By default the labs are pointed at a local stub (fake_anthropic.py) through
ANTHROPIC_BASE_URL, so a full pass is free, deterministic and safe to run on
every change. Every lab builds its client as a bare `anthropic.Anthropic()`,
which reads that variable, so nothing in the labs needs editing.

    python labs/harness/run_labs.py              # stub, free
    python labs/harness/run_labs.py --live       # real API -- SPENDS MONEY
    python labs/harness/run_labs.py --only M05

--live requires ANTHROPIC_API_KEY already in the environment. It is never
implied: without --live the key is replaced with a dummy so a real one cannot
be spent by accident.

A stub pass means the code is sound -- valid requests, working tool-use round
trip, correct reading of content blocks and stop_reason, completion. It says
nothing about answer quality, so labs whose subject IS the answer (evals,
judges, guardrail decisions) are only truly checked under --live.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
STUB_PORT = 8787

# Scripts that block on stdin cannot be run unattended. They are reported, not
# silently dropped, so the count never overstates what was actually exercised.
INTERACTIVE = re.compile(r"\binput\s*\(")


def uses_anthropic(src: str) -> bool:
    if "ANTHROPIC_API_KEY" in src:
        return True
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[0] == "anthropic" for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "anthropic":
                return True
    return False


def candidates() -> list[tuple[Path, str, bool]]:
    out = []
    for s in sorted(LABS.rglob("solution/*.py")):
        if s.name == "__init__.py" or "__pycache__" in s.parts or HERE in s.parents:
            continue
        src = s.read_text(encoding="utf-8", errors="replace")
        if not uses_anthropic(src) or "__main__" not in src:
            continue
        out.append((s, str(s.relative_to(LABS)).replace("\\", "/"),
                    bool(INTERACTIVE.search(src))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="call the real Anthropic API (SPENDS MONEY; needs ANTHROPIC_API_KEY)")
    ap.add_argument("--only", default="")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--results", default="")
    args = ap.parse_args()

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    server = None
    if args.live:
        if not env.get("ANTHROPIC_API_KEY"):
            print("--live needs ANTHROPIC_API_KEY in the environment", file=sys.stderr)
            return 2
        print("mode: LIVE — real Anthropic API, this run costs money\n", flush=True)
    else:
        sys.path.insert(0, str(HERE))
        from fake_anthropic import serve      # noqa: E402
        try:
            server = serve(STUB_PORT)
        except OSError as exc:
            print(f"could not bind the stub on {STUB_PORT}: {exc}", file=sys.stderr)
            return 2
        # Override the key too: a real one in the environment must not be
        # spendable from a run that never intended to spend it.
        env["ANTHROPIC_BASE_URL"] = f"http://localhost:{STUB_PORT}"
        env["ANTHROPIC_API_KEY"] = "stub-not-a-real-key"
        print("mode: STUB (canned replies; proves plumbing, not answer quality)\n", flush=True)

    work = [(p, rel, inter) for p, rel, inter in candidates() if args.only in rel]
    width = max((len(r) for _, r, _ in work), default=10)
    log = HERE / (args.results or ("results-live.txt" if args.live else "results-stub.txt"))
    log.write_text(f"# mode={'live' if args.live else 'stub'}\n", encoding="utf-8")

    print(f"{'':4s}  {'solution':{width}s}  secs", flush=True)
    rows, failures = [], []
    for script, rel, interactive in work:
        if interactive:
            rows.append(("SKIP", rel))
            line = f"{'SKIP':4s}  {rel:{width}s}     - reads stdin"
            print(line, flush=True)
            log.open("a", encoding="utf-8").write(line + "\n")
            continue
        started = time.time()
        try:
            proc = subprocess.run([sys.executable, script.name], cwd=script.parent,
                                  capture_output=True, text=True, errors="replace",
                                  timeout=args.timeout, env=env)
            rc, out = proc.returncode, (proc.stderr or proc.stdout) or ""
        except subprocess.TimeoutExpired:
            rc, out = -1, f"exceeded --timeout of {args.timeout}s"
        secs = time.time() - started

        status = "PASS" if rc == 0 else "FAIL"
        if rc != 0:
            tail = [l for l in out.strip().splitlines() if l.strip()]
            failures.append((rel, tail[-1][:130] if tail else "(no output)"))
        rows.append((status, rel))
        line = f"{status:4s}  {rel:{width}s}  {secs:5.0f}"
        print(line, flush=True)
        log.open("a", encoding="utf-8").write(line + "\n")

    if server is not None:
        server.shutdown()

    n = lambda k: sum(1 for s, _ in rows if s == k)   # noqa: E731
    print(f"\n{n('PASS')} passed, {n('FAIL')} failed, {n('SKIP')} skipped (interactive), "
          f"{len(rows)} total")
    for rel, msg in failures:
        print(f"\nFAIL {rel}\n     {msg}")
    return 1 if n("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
