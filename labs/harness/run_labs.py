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


# These labs catch API errors, print a friendly line and exit 0 -- good for a
# student, useless for a harness, because a completely failed run still looks
# like a pass. Exit status alone cannot tell "worked" from "failed politely".
#
# Match API failures specifically, not any error text. A bare "Traceback" or
# "[ERROR]" is not evidence: M15 is a code-interpreter sandbox whose whole job
# is to run code that raises, so its correct output contains both. Flagging that
# as an API problem is the same mistake in the other direction -- a false defect
# instead of a false pass.
TROUBLE = re.compile(
    r"Invalid API key|authentication_error|permission_error|not_found_error|"
    r"model_not_found|rate_limit_error|insufficient|credit balance|"
    r"overloaded_error|invalid_request_error|APIConnectionError|"
    r"APIStatusError|AuthenticationError", re.I)


def preflight(env: dict) -> tuple[bool, str]:
    """One cheap call, before spending anything on a full sweep.

    Catches the two ways a live run silently produces nothing of value: a key
    that does not authenticate, and a model id the account cannot serve. Both
    would otherwise show up as a page of PASSes, since the labs swallow their
    own API errors.
    """
    default_model = "claude-sonnet-4-6"
    code = (
        "import os,sys,json\n"
        "import anthropic\n"
        "m=os.environ.get('PREFLIGHT_MODEL')\n"
        "try:\n"
        "    r=anthropic.Anthropic().messages.create(model=m,max_tokens=4,\n"
        "        messages=[{'role':'user','content':'hi'}])\n"
        "    print('OK '+r.model)\n"
        "except Exception as e:\n"
        "    print(type(e).__name__+': '+str(e)[:180]); sys.exit(1)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          timeout=120, env=dict(env, PREFLIGHT_MODEL=default_model))
    out = (proc.stdout or proc.stderr or "").strip().splitlines()
    line = out[-1] if out else "(no output)"
    if proc.returncode == 0 and line.startswith("OK"):
        return True, f"key authenticates, {default_model} served (as {line[3:]})"
    return False, line


def candidates() -> tuple[list[tuple[Path, str, bool]], list[tuple[str, str]]]:
    """Returns (runnable, unparseable).

    A file that will not parse is returned rather than skipped. uses_anthropic()
    answers False for it, so a silent skip would quietly shrink the run: a
    solution broken badly enough to be a syntax error would vanish from the
    report entirely, and the totals would look normal. That is the worst
    possible way for this harness to fail.
    """
    out, broken = [], []
    for s in sorted(LABS.rglob("solution/*.py")):
        if s.name == "__init__.py" or "__pycache__" in s.parts or HERE in s.parents:
            continue
        src = s.read_text(encoding="utf-8", errors="replace")
        rel = str(s.relative_to(LABS)).replace("\\", "/")
        try:
            ast.parse(src)
        except SyntaxError as exc:
            broken.append((rel, f"does not parse: {exc.msg} (line {exc.lineno})"))
            continue
        if not uses_anthropic(src) or "__main__" not in src:
            continue
        out.append((s, rel, bool(INTERACTIVE.search(src))))
    return out, broken


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="call the real Anthropic API (SPENDS MONEY; needs ANTHROPIC_API_KEY)")
    ap.add_argument("--only", default="")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--results", default="")
    args = ap.parse_args()

    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    # labs/.env is the documented place for the key (see .env.example) and is
    # gitignored. Reading it here means the key never has to be exported into a
    # shell, where it would sit in history. Parsed by hand rather than via
    # python-dotenv so the harness has no dependency the labs do not already
    # have, and so a stray value never overwrites something already exported.
    dotenv = LABS / ".env"
    if dotenv.is_file():
        # utf-8-sig, not utf-8: Windows PowerShell's `Set-Content -Encoding utf8`
        # writes a BOM, which otherwise makes the first key parse as
        # "﻿ANTHROPIC_API_KEY" and go unnoticed -- the harness then reports
        # "no key" while staring straight at one.
        for line in dotenv.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in env:
                env[k] = v

    server = None
    if args.live:
        if not env.get("ANTHROPIC_API_KEY"):
            print("--live needs ANTHROPIC_API_KEY: export it, or put it in labs/.env "
                  "(gitignored; see labs/.env.example)", file=sys.stderr)
            return 2
        ok, detail = preflight(env)
        if not ok:
            print(f"pre-flight failed, refusing to start: {detail}", file=sys.stderr)
            return 2
        print(f"mode: LIVE — real Anthropic API, this run costs money")
        print(f"pre-flight OK: {detail}\n", flush=True)
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

    discovered, broken = candidates()
    work = [(p, rel, inter) for p, rel, inter in discovered if args.only in rel]
    width = max((len(r) for _, r, _ in work), default=10)
    log = HERE / (args.results or ("results-live.txt" if args.live else "results-stub.txt"))
    log.write_text(f"# mode={'live' if args.live else 'stub'}\n", encoding="utf-8")

    print(f"{'':4s}  {'solution':{width}s}  secs", flush=True)
    rows, failures = [], []
    for rel, why in broken:
        if args.only not in rel:
            continue
        rows.append(("FAIL", rel))
        failures.append((rel, why))
        line = f"{'FAIL':4s}  {rel:{width}s}      - {why}"
        print(line, flush=True)
        log.open("a", encoding="utf-8").write(line + "\n")
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

        combined = ((proc.stdout or "") + (proc.stderr or "")) if rc != -1 else out

        # An exhausted balance is not a lab result, and every remaining script
        # would report the same thing -- turning one budget problem into a page
        # of failures that look like defects. Pre-flight cannot catch this: a
        # four-token probe still fits in the last few cents. Stop here instead
        # and say so, so the run is not mistaken for evidence about the labs.
        if re.search(r"credit balance is too low", combined, re.I):
            print(f"\nABORTED at {rel}: the account's credit balance is exhausted.\n"
                  f"Everything already recorded above stands; nothing after this point "
                  f"would have been a test of the labs.", flush=True)
            log.open("a", encoding="utf-8").write(
                f"# ABORTED at {rel}: credit balance exhausted\n")
            rows.append(("FAIL", rel))
            failures.append((rel, "credit balance exhausted — run aborted"))
            break
        if rc == 0 and TROUBLE.search(combined):
            # Exit 0 but the output confesses an API failure. Reporting this as
            # PASS is how a whole live sweep can look green while nothing ever
            # reached the API.
            status = "WARN"
            hit = TROUBLE.search(combined)
            ctx = combined[max(0, hit.start() - 40): hit.end() + 90].replace("\n", " ")
            failures.append((rel, f"exit 0 but output reports: …{ctx.strip()}"))
        elif rc == 0:
            status = "PASS"
        else:
            status = "FAIL"
            tail = [l for l in out.strip().splitlines() if l.strip()]
            failures.append((rel, tail[-1][:130] if tail else "(no output)"))
        rows.append((status, rel))
        line = f"{status:4s}  {rel:{width}s}  {secs:5.0f}"
        print(line, flush=True)
        log.open("a", encoding="utf-8").write(line + "\n")

    if server is not None:
        server.shutdown()

    n = lambda k: sum(1 for s, _ in rows if s == k)   # noqa: E731
    print(f"\n{n('PASS')} passed, {n('WARN')} exited 0 but reported an API error, "
          f"{n('FAIL')} failed, {n('SKIP')} skipped (interactive), {len(rows)} total")
    for rel, msg in failures:
        tag = "WARN" if msg.startswith("exit 0") else "FAIL"
        print(f"\n{tag} {rel}\n     {msg}")
    # WARN is a failure for CI purposes: a green sweep in which nothing reached
    # the API is the exact outcome this harness exists to prevent.
    return 1 if (n("FAIL") or n("WARN")) else 0


if __name__ == "__main__":
    sys.exit(main())
