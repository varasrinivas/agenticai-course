#!/usr/bin/env python3
"""
M19 Lab - Step 3: Trace Viewer (COMPLETE — just run it)
========================================================
CLI pretty-printer for agent JSONL trace files.

Usage:
    python trace_viewer.py traces/trace_a3f7b2.jsonl
    python trace_viewer.py traces/trace_a3f7b2.jsonl --slow-threshold 1000
"""

import argparse
import json
import sys
from pathlib import Path

RED = "\033[91m"; YELLOW = "\033[93m"; GREEN = "\033[92m"
CYAN = "\033[96m"; DIM = "\033[2m"; RESET = "\033[0m"; BOLD = "\033[1m"

CATEGORY_COLOR = {
    "llm_turn": YELLOW, "tool_call": GREEN,
    "error": RED, "loop_iter": CYAN,
}


def load_events(filepath: str) -> list[dict]:
    events = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # skip corrupt lines, never crash the viewer
    return events


def print_call_tree(events: list[dict], slow_ms: float = 2000) -> None:
    print(f"\n{BOLD}{'-' * 60}{RESET}")
    print(f"{BOLD}TRACE: {events[0].get('run_id', 'unknown')}{RESET}")
    print("-" * 60)
    for ev in events:
        cat = ev.get("category", "unknown")
        color = CATEGORY_COLOR.get(cat, RESET)
        latency = ev.get("latency_ms", 0) or 0
        slow = f" {RED}SLOW{RESET}" if latency > slow_ms else ""

        if cat == "llm_turn":
            print(f"  {color}LLM [{ev.get('model', '?')}]{RESET}  "
                  f"{DIM}{ev.get('prompt_tokens', '?')}->{ev.get('completion_tokens', '?')} tok  "
                  f"{ev.get('finish_reason', '?')}{RESET}  "
                  f"{YELLOW}{latency:.0f}ms{RESET}{slow}")
        elif cat == "tool_call":
            ok = ev.get("tool_ok", True)
            status = f"{GREEN}ok{RESET}" if ok else f"{RED}ERR {str(ev.get('tool_error', ''))[:40]}{RESET}"
            print(f"    {color}TOOL {ev.get('tool_name', '?')}{RESET}  "
                  f"{status}  {YELLOW}{latency:.0f}ms{RESET}{slow}")
        elif cat == "loop_iter":
            print(f"  {color}-- iter {ev.get('iteration', '?')} "
                  f"[{ev.get('exit_reason', '?')}] "
                  f"tools={ev.get('tools_invoked', [])} "
                  f"{YELLOW}{latency:.0f}ms{RESET}{slow}")
        elif cat == "error":
            print(f"  {RED}ERROR {ev.get('exc_type', '?')}: "
                  f"{str(ev.get('exc_msg', ''))[:80]}{RESET}")
    print("-" * 60)


def print_summary(events: list[dict], slow_ms: float) -> None:
    by_cat: dict[str, list[float]] = {}
    for ev in events:
        by_cat.setdefault(ev.get("category", "?"), []).append(ev.get("latency_ms") or 0)

    print(f"\n{BOLD}Category breakdown:{RESET}")
    print(f"{'category':<12} {'count':>5} {'avg_latency_ms':>15}")
    for cat, lats in sorted(by_cat.items()):
        avg = sum(lats) / len(lats) if lats else 0
        print(f"{cat:<12} {len(lats):>5} {avg:>15.1f}")

    slow = [e for e in events if (e.get("latency_ms") or 0) > slow_ms]
    if slow:
        print(f"\n{RED}Slow steps (>{slow_ms:.0f}ms):{RESET}")
        for e in slow:
            name = e.get("tool_name") or e.get("model") or ""
            print(f"  {e.get('category')}: {name}  {e.get('latency_ms', 0):.0f}ms")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tracefile")
    parser.add_argument("--slow-threshold", type=float, default=2000)
    args = parser.parse_args()

    if not Path(args.tracefile).exists():
        print(f"File not found: {args.tracefile}", file=sys.stderr)
        sys.exit(1)

    events = load_events(args.tracefile)
    if not events:
        print("Trace file is empty.", file=sys.stderr)
        sys.exit(1)

    print_call_tree(events, slow_ms=args.slow_threshold)
    print_summary(events, args.slow_threshold)


if __name__ == "__main__":
    main()
