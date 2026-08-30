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
    ap.add_argument("--resume", action="store_true",
                    help="skip labs already recorded in the results file and append to it")
    ap.add_argument("--results", default="",
                    help="results filename (default results-live.txt / results-stub.txt). "
                         "Use a distinct file when a run is served by a different model, so "
                         "one model's results never land in another's log")
    args = ap.parse_args()

    server = None
    if args.live:
        if not endpoint_alive():
            print("nothing is serving http://localhost:11434 — start Ollama "
                  "(`ollama serve`) and `ollama pull mistral`, or drop --live", file=sys.stderr)
            return 2
        print("mode: LIVE (real model on :11434)\n")
    else:
        if endpoint_alive(1.0):
            print("something is already serving http://localhost:11434 — most likely a real\n"
                  "Ollama, or a stub left over from an earlier run. The stub cannot take the\n"
                  "port, and letting it appear to start would mean these results came from a\n"
                  "server this run does not control.\n\n"
                  "  ->  pass --live to use whatever is serving, or stop it and re-run.",
                  file=sys.stderr)
            return 2
        sys.path.insert(0, str(HERE))
        from fake_ollama import serve      # noqa: E402
        try:
            server = serve()
        except OSError as exc:
            print(f"could not bind port 11434 for the stub: {exc}", file=sys.stderr)
            return 2
        for _ in range(40):
            if endpoint_alive(0.5):
                break
            time.sleep(0.1)
        print("mode: STUB (canned replies; proves plumbing, not answer quality)\n")

    scripts = [(s, r) for s, r in declared_scripts() if args.only in r]
    width = max((len(r) for _, r in scripts), default=10)
    rows, failures = [], []

    # Results are printed and appended to the log AS THEY HAPPEN, not collected
    # and dumped at the end. --live is minutes per lab (CPU inference runs about
    # 40s per model call), so a run that is interrupted after an hour must still
    # leave behind everything it learned. Buffering the table to the end means a
    # kill throws all of it away.
    log = HERE / (args.results or ("results-live.txt" if args.live else "results-stub.txt"))
    done: set[str] = set()
    if args.resume and log.is_file():
        # A live sweep is long enough to be interrupted, so allow picking it up
        # where it stopped: anything already recorded is not worth 40s/call to
        # re-prove. Parse column 2 of each result line back out of the log.
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ("PASS", "FAIL", "TODO"):
                done.add(parts[1])
        print(f"resuming: {len(done)} lab(s) already recorded, skipping them\n", flush=True)
    else:
        log.write_text(f"# mode={'live' if args.live else 'stub'}\n", encoding="utf-8")

    print(f"{'':4s}  {'lab script':{width}s}  kind      secs", flush=True)

    for script, rel in scripts:
        if rel in done:
            continue
        needs = wants_model(script)
        started = time.time()
        try:
            proc = subprocess.run([sys.executable, script.name], cwd=script.parent,
                                  capture_output=True, text=True, errors="replace",
                                  timeout=args.timeout,
                                  env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            rc, out = proc.returncode, (proc.stderr or proc.stdout) or ""
        except subprocess.TimeoutExpired:
            rc, out = -1, f"exceeded --timeout of {args.timeout}s"
        secs = time.time() - started

        expected = rel in EXPECTED_FAILURES
        if rc == 0:
            status = "PASS"
        elif expected:
            status = "TODO"                 # designed to fail until implemented
        else:
            status = "FAIL"
            tail = [l for l in out.strip().splitlines() if l.strip()]
            failures.append((rel, tail[-1][:130] if tail else "(no output)"))
        rows.append((status, rel, "model" if needs else "offline"))

        line = f"{status:4s}  {rel:{width}s}  {'model' if needs else 'offline':7s} {secs:6.0f}"
        print(line, flush=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    if server is not None:
        server.shutdown()

    n_pass = sum(1 for s, _, _ in rows if s == "PASS")
    n_todo = sum(1 for s, _, _ in rows if s == "TODO")
    n_fail = sum(1 for s, _, _ in rows if s == "FAIL")
    print(f"\nthis run: {n_pass} passed, {n_todo} unimplemented starter(s), "
          f"{n_fail} failed, {len(rows)} total")

    # With --resume the rows above are only the current batch, so report the
    # whole log too -- otherwise a resumed sweep looks like it covered far less
    # than it did.
    tally: dict[str, int] = {}
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        head = line.split(" ", 1)[0]
        if head in ("PASS", "FAIL", "TODO"):
            tally[head] = tally.get(head, 0) + 1
    total = sum(tally.values())
    if total != len(rows):
        # denominator is every declared script, not the --only subset, or a
        # batched sweep reports "17 of 1"
        print(f"cumulative in {log.name}: {tally.get('PASS', 0)} passed, "
              f"{tally.get('TODO', 0)} unimplemented starter(s), "
              f"{tally.get('FAIL', 0)} failed, {total} of "
              f"{len(declared_scripts())} declared")
    for rel, msg in failures:
        print(f"\nFAIL {rel}\n     {msg}")
    for rel, why in EXPECTED_FAILURES.items():
        if any(r == rel and s == "TODO" for s, r, _ in rows):
            print(f"\nTODO {rel}\n     {why}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
