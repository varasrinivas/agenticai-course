"""Evaluation harness for the migration agent.

Twenty scenarios across five categories. Pass threshold is 18/20 -- not 20,
because two of the cases (PLSQL-03 and VALIDATE-01) reward the agent for
*refusing* or for *reporting a defect*, and an agent that is calibrated
slightly conservatively will occasionally refuse something it could have
handled. That is the failure direction you want.

Run:  python evaluation/test_suite.py
      python evaluation/test_suite.py --category guardrail
      python evaluation/test_suite.py --offline     (no API calls; checks fixtures)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, query  # noqa: E402

import config  # noqa: E402
import hooks  # noqa: E402
from tools_local import local_server  # noqa: E402
from tools_oracle import oracle_server  # noqa: E402
from tools_postgres import pg_server  # noqa: E402

CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")


@dataclass
class Result:
    case_id: str
    category: str
    passed: bool
    detail: str


def _load() -> dict:
    with open(CASES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _check_text(case: dict, text: str) -> tuple[bool, str]:
    """String-level assertions. Deliberately case-insensitive substring
    checks rather than exact matches -- we are scoring whether the agent
    reached the right conclusion, not whether it formatted the SQL the way
    we would have."""
    lowered = text.lower()
    problems: list[str] = []

    for needle in case.get("expect_contains", []):
        if needle.lower() not in lowered:
            problems.append(f"missing {needle!r}")

    for needle in case.get("expect_absent", []):
        if needle.lower() in lowered:
            problems.append(f"should not contain {needle!r}")

    if case.get("expect_refusal") and not any(
        marker in lowered
        for marker in ("manual review", "manual_review", "cannot", "refuse", "no equivalent")
    ):
        problems.append("expected a refusal, got an attempted conversion")

    if case.get("expect_denied") and not any(
        marker in lowered for marker in ("deny", "denied", "refused", "rejected", "read-only")
    ):
        problems.append("expected the guardrail to deny this")

    if case.get("expect_defect") and not any(
        marker in lowered for marker in ("defect", "divergen", "mismatch", "failed")
    ):
        problems.append("expected a reported defect, got a clean result")

    return (not problems), "; ".join(problems) or "ok"


async def _ask(case: dict) -> str:
    options = ClaudeAgentOptions(
        model=config.COORDINATOR_MODEL,
        system_prompt=(
            "You are evaluating one migration scenario. Answer with the "
            "PostgreSQL translation, the guardrail decision, or the validation "
            "finding -- whichever the scenario calls for. Be concrete and show "
            "the SQL. If the correct answer is that something cannot be "
            "translated safely, say so and say why."
        ),
        max_turns=6,
        mcp_servers={
            "oracle_src": oracle_server,
            "pg_target": pg_server,
            "migration_local": local_server,
        },
        can_use_tool=hooks.can_use_tool,
    )

    chunks: list[str] = []
    prompt = f"{case['input']}\n\nContext: {case.get('why', '')}"
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                text = getattr(block, "text", None)
                if text:
                    chunks.append(text)
    return "\n".join(chunks)


async def run(category: str | None = None, offline: bool = False) -> int:
    suite = _load()
    cases = [c for c in suite["cases"] if not category or c["category"] == category]

    print(f"\n{suite['suite']}")
    print(f"Running {len(cases)} of {suite['total']} cases"
          f"{f' (category={category})' if category else ''}"
          f"{' [OFFLINE]' if offline else ''}\n")

    results: list[Result] = []
    for case in cases:
        if offline:
            # Offline mode only verifies the suite itself is well-formed --
            # useful in CI where no API key is available.
            ok = bool(case.get("expect_contains") or case.get("expect_denied")
                      or case.get("expect_refusal") or case.get("expect_defect")
                      or case.get("expect_row_match") or case.get("expect_null_match")
                      or case.get("expect_value"))
            results.append(Result(case["id"], case["category"], ok,
                                  "well-formed" if ok else "no assertion defined"))
            continue

        try:
            answer = await _ask(case)
            passed, detail = _check_text(case, answer)
        except Exception as exc:                       # noqa: BLE001
            passed, detail = False, f"{type(exc).__name__}: {exc}"

        results.append(Result(case["id"], case["category"], passed, detail))
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {case['id']:<12} {detail}")

    passed_count = sum(1 for r in results if r.passed)
    threshold = suite["pass_threshold"] if not category else max(1, int(len(cases) * 0.9))

    print(f"\n{'=' * 62}")
    print(f"  {passed_count}/{len(cases)} passed (threshold {threshold})")

    by_category: dict[str, list[Result]] = {}
    for result in results:
        by_category.setdefault(result.category, []).append(result)
    for name, group in sorted(by_category.items()):
        good = sum(1 for r in group if r.passed)
        print(f"    {name:<12} {good}/{len(group)}")

    failures = [r for r in results if not r.passed]
    if failures:
        print("\n  Failures:")
        for result in failures:
            print(f"    {result.case_id}: {result.detail}")
    print("=" * 62 + "\n")

    return 0 if passed_count >= threshold else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="CAPSTONE-8 evaluation harness")
    parser.add_argument("--category", choices=["schema", "data", "plsql", "appsql",
                                               "guardrail", "validation"])
    parser.add_argument("--offline", action="store_true",
                        help="validate the suite without calling the API")
    args = parser.parse_args()
    return asyncio.run(run(args.category, args.offline))


if __name__ == "__main__":
    sys.exit(main())
