"""Run every lab script this course documents, and report which ones still run.

Each lab's expected_output/sample_output.txt opens its blocks with the command
that produced them:

    $ python solution/extractor.py

so the samples themselves are the list of things worth running. This collects
those declarations, executes each one, and prints a table.

Two modes:

  --stub  (default)  Serve a canned model on :11434 via fake_ollama.py.
                     Deterministic, free, no model download, CI-friendly.
                     Verifies that a lab imports, builds a well-formed request,
                     survives the tool-call round trip, parses the reply and
                     reaches the end of its own demo.
                     It does NOT verify that a real model answers well: the
                     stub's replies are canned, so a lab whose point is answer
                     QUALITY will pass here regardless.

  --live             Use whatever is already serving :11434 — i.e. real Ollama
                     with `ollama pull mistral`. This is the mode that checks
                     the labs' claims about model behaviour. Output text varies
                     between runs, so treat it as "did it complete", not a diff.

Usage:
    python harness/run_labs.py                # stub
    python harness/run_labs.py --live         # real Ollama
    python harness/run_labs.py --only M04     # substring filter
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
BLOCK = re.compile(r"^\s*\$\s*(?:python3?)\s+(\S+\.py)([^\n]*)$", re.M)
NETWORK = re.compile(r"\b(anthropic|openai|mistralai|ollama|cohere|voyageai|httpx|requests)\b")

# Starters ship deliberate TODOs, so they are expected to fail until the reader
# fills them in. Listing them keeps a designed failure from reading as a defect.
EXPECTED_FAILURES = {
    "M03B-context-engineering/starter/diagnose.py":
        "starter: context_budget.account() is a TODO, so the breakdown is None until you write it",
}


def declared_scripts() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for sample in sorted(LABS.rglob("expected_output/sample_output.txt")):
        lab = sample.parent.parent
        for m in BLOCK.finditer(sample.read_text(encoding="utf-8", errors="replace")):
            if m.group(2).strip():
                continue                      # takes CLI args; not a bare run
            script = lab / m.group(1)
            if script.is_file():
                found.append((script, str(script.relative_to(LABS)).replace("\\", "/")))
    return found


def wants_model(script: Path) -> bool:
    src = script.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(NETWORK.match(a.name.split(".")[0]) for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and NETWORK.match(node.module.split(".")[0]):
                return True
    return False


def endpoint_alive(timeout: float = 3.0) -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout).read()
        return True
    except (urllib.error.URLError, OSError):
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="use the Ollama already serving :11434 instead of the stub")
    ap.add_argument("--only", default="", help="substring filter on the lab path")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    server = None
    if args.live:
        if not endpoint_alive():
            print("nothing is serving http://localhost:11434 — start Ollama "
                  "(`ollama serve`) and `ollama pull mistral`, or drop --live", file=sys.stderr)
            return 2
        print("mode: LIVE (real model on :11434)\n")
    else:
        sys.path.insert(0, str(HERE))
        from fake_ollama import serve      # noqa: E402
        server = serve()
        for _ in range(40):
            if endpoint_alive(0.5):
                break
            time.sleep(0.1)
        print("mode: STUB (canned replies; proves plumbing, not answer quality)\n")

    scripts = [(s, r) for s, r in declared_scripts() if args.only in r]
    rows, failures = [], []
    for script, rel in scripts:
        needs = wants_model(script)
        proc = subprocess.run([sys.executable, script.name], cwd=script.parent,
                              capture_output=True, text=True, errors="replace",
                              timeout=args.timeout,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        expected = rel in EXPECTED_FAILURES
        if proc.returncode == 0:
            status = "PASS"
        elif expected:
            status = "TODO"                 # designed to fail until implemented
        else:
            status = "FAIL"
            tail = [l for l in ((proc.stderr or proc.stdout) or "").strip().splitlines() if l.strip()]
            failures.append((rel, tail[-1][:130] if tail else "(no output)"))
        rows.append((status, rel, "model" if needs else "offline"))

    if server is not None:
        server.shutdown()

    width = max((len(r) for _, r, _ in rows), default=10)
    print(f"{'':4s}  {'lab script':{width}s}  kind")
    for status, rel, kind in rows:
        print(f"{status:4s}  {rel:{width}s}  {kind}")

    n_pass = sum(1 for s, _, _ in rows if s == "PASS")
    n_todo = sum(1 for s, _, _ in rows if s == "TODO")
    n_fail = sum(1 for s, _, _ in rows if s == "FAIL")
    print(f"\n{n_pass} passed, {n_todo} unimplemented starter(s), {n_fail} failed, {len(rows)} total")
    for rel, msg in failures:
        print(f"\nFAIL {rel}\n     {msg}")
    for rel, why in EXPECTED_FAILURES.items():
        if any(r == rel and s == "TODO" for s, r, _ in rows):
            print(f"\nTODO {rel}\n     {why}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
