"""Modernization coordinator.

Six phases, in order, each gated on the previous one:

    1 map            read the reference platform -> architecture manifest
    2 excavate       read the monolith and its views -> domain model, seam map,
                     screen inventory
    3 extract_rules  the level-of-care rules -> decision-table IR
    4 gap_analyse    the gap register  <- THE DELIVERABLE
    5 synthesize     emit bh-um-lite/
    6 validate       prove it, or say exactly where it is not proven
    (finalize)       human-gated, never automatic

Run everything:   python coordinator.py --phase all
Backend only:     python coordinator.py --phase 9a
Frontend only:    python coordinator.py --phase 9b   (gated on 9a being green)
One phase:        python coordinator.py --phase extract_rules
Resume:           python coordinator.py --phase all --resume
Finalize:         python coordinator.py --phase finalize --approve

THE COORDINATOR HAS NO FILE TOOLS. Every read goes through a subagent with its
own context window, so one phase's reading does not crowd out the next phase's
reasoning. This process sequences, checks that each phase produced what it
claimed, and reports.
"""

# =============================================================================
# GIVEN COMPLETE. Read it, do not rewrite it.
#
# This file is plumbing, not the lesson. Your work is in the files carrying
# numbered TODOs -- run `grep -rn "TODO [0-9]" starter/` to list them in order.
# =============================================================================


from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, HookMatcher,
                              query)

import config
import hooks
from gap_register import GapRegister
from observability import Metrics, Tracer
from session import ModernizationSession
from tools_emit import local_server
from tools_legacy import legacy_server
from tools_reference import reference_server

COORDINATOR_PROMPT = """\
You are the coordinator for a behavioral-health utilization-management
modernization at a health plan that has in-sourced a carve-out vendor's system.

Two source trees, both READ-ONLY and enforced in code:
  reference-umlite/  the clinical UM platform. Architecture donor.
  bhauthtrack/       a 2011 Spring MVC/JSP monolith. Domain donor.

Everything you produce goes under bh-um-lite/.

YOUR JOB IS NOT "TRANSLATE THE CODE". It is: port the architecture AND detect
where the donor architecture is insufficient for behavioral health. The
deliverable is a working repository AND a gap register.

Work in six phases and do not start one until the previous reports success.
Never call a file tool yourself -- always delegate to the specialist subagent.

Rules that are not negotiable:

- When a specialist refuses to convert something and queues it for human
  review, that is a SUCCESS. Record it and move on. Do not try to convert it
  yourself and do not ask the specialist to try harder.
- A run that queues nothing has guessed at something. BH_AUTH.LEGACY_OVERRIDE
  is undocumented and set on hundreds of live rows.
- A clean result from the parity validator on rules divergence, protected
  content, narrative round-trip or consent atomicity is SUSPICIOUS. Report it
  as suspicious rather than as a pass.
- You may not call finalize_modernization successfully. It is human-gated. When
  it denies, that is the expected end of the run: report what a person has to
  decide, and stop.
"""

PHASE_PROMPTS = {
    "map": (
        "Delegate to architecture-cartographer. It must open the migrations, the "
        "intake DTO, the decision table, the process model, the review task, the "
        "audit story, the authorization model, the PHI handling, the test suite, "
        "the feature flags and the frontend -- and report a tag for each with a "
        "one-line reason. Report the counts it found and every capability tagged "
        "insufficient-for-bh."
    ),
    "excavate": (
        "Delegate to monolith-archaeologist AND jsp-archaeologist. The first "
        "produces the domain model, the seam map and the unknowns queue; the "
        "second treats the JSPs as a source of RULES and produces the screen "
        "inventory. Report the recommended seam, what replaces the atomicity it "
        "breaks, how many call paths reach each decision method, and every rule "
        "found in a view whose server-side equivalent is NONE."
    ),
    "extract_rules": (
        "Delegate to rules-extractor. The rules are in TWO places -- an Oracle "
        "package and a Java service that runs after it -- and neither alone is "
        "the rule set. It must classify every branch as committing or "
        "accumulating, run the overlap checker, choose a hit policy and justify "
        "it in writing, then diff both engines over the golden set. Report the "
        "policy, its justification, every overlapping pair with its resolution, "
        "and the divergence count with each divergence classified."
    ),
    "gap_analyse": (
        "Delegate to gap-analyst. Every capability gets exactly one verdict with "
        "cited evidence; must-not-port requires a named harm. Cross-check "
        "against the platform team's own backlog and report agreements and "
        "disagreements as SEPARATE lists. Report the verdict distribution."
    ),
    "synthesize": (
        "Delegate to repo-synthesizer. The gap register is binding: implement "
        "every must-build-new item rather than deferring it, and emit nothing "
        "marked must-not-port. Report files emitted by area, where each "
        "must-build-new item landed, and anything in the register you could NOT "
        "implement -- named, with the reason."
    ),
    "validate": (
        "Delegate to parity-validator, phase 9a -- check 8 belongs to the "
        "frontend phase. Checks 1-4 are the four a naive port trips. A clean "
        "result from one of them is not a problem by itself; what matters is "
        "whether the check COULD HAVE FIRED, so report what each one scanned. "
        "State plainly whether the run is ready for the finalization gate."
    ),

    # ---- phase 9B. Gated on 9A being green: the screen inventory and the
    # rules-found-in-views list are its inputs, and a client cannot supply an
    # enforcement the backend does not have.
    "synthesize_frontend": (
        "Delegate to frontend-synthesizer. Its input is the screen inventory "
        "from phase 2. Every screen gets a REACHABLE route -- reachable, not "
        "merely defined. Every rule the JSP archaeologist extracted from a view "
        "must land in a route guard, a server-side check, a computed field, an "
        "API omission or a workflow candidate group; a rule re-implemented as a "
        "template conditional has not moved. Report the route table, where each "
        "rule landed, and every rule whose server-side enforcement is MISSING "
        "in 9A's output -- named, because those fail validation for a reason "
        "that is not the client's."
    ),
    "validate_frontend": (
        "Delegate to parity-validator, phase 9b. Check 8: every legacy screen "
        "routable, every view rule relocated, the shared component library "
        "consumed rather than orphaned, no numeric role comparison carried over "
        "from JSTL, and no hardcoded service URL. Report each finding with its "
        "file."
    ),
}


def _options(system_prompt: str, model: str, allowed: list[str] | None = None):
    """One place where every SDK knob is set, so a caller cannot forget a guard."""
    return ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        max_turns=config.MAX_TURNS,
        mcp_servers={
            "reference_src": reference_server,
            "legacy_src": legacy_server,
            "local": local_server,
        },
        allowed_tools=allowed,
        can_use_tool=hooks.can_use_tool,
        hooks={"PostToolUse": [HookMatcher(matcher="*", hooks=[hooks.audit_log])]},
    )


async def _run(prompt: str, *, system_prompt: str, model: str, tracer: Tracer,
               label: str, budget: hooks.TokenBudget) -> str:
    chunks: list[str] = []
    message = None
    with tracer.span(label) as span:
        async for message in query(prompt=prompt,
                                   options=_options(system_prompt, model)):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    text = getattr(block, "text", None)
                    if text:
                        chunks.append(text)
        usage = getattr(message, "usage", None)
        tokens = getattr(usage, "output_tokens", 0) if usage else 0
        budget.add(tokens)
        span.tokens = tokens
    return "\n".join(chunks)


class Modernization:
    def __init__(self, session: ModernizationSession, tracer: Tracer):
        self.session = session
        self.tracer = tracer
        self.budget = hooks.TokenBudget()
        self.breaker = hooks.CircuitBreaker()
        self.metrics = Metrics()

    # ------------------------------------------------------------- phases
    async def run_phase(self, phase: str) -> str:
        if phase not in PHASE_PROMPTS:
            raise ValueError(f"unknown phase {phase!r}")

        if phase in config.PHASES_9A:
            label = f"PHASE {config.PHASES_9A.index(phase) + 1}/6"
        else:
            label = f"PHASE 9B.{config.PHASES_9B.index(phase) + 1}/2"
        print(f"\n=== {label}  {phase.upper()} " + "=" * max(4, 40 - len(phase)))

        self.tracer.phase = phase
        model = (config.MECHANICAL_MODEL
                 if phase in ("validate", "validate_frontend")
                 else config.REASONING_MODEL)
        try:
            result = await _run(PHASE_PROMPTS[phase],
                                system_prompt=COORDINATOR_PROMPT,
                                model=model, tracer=self.tracer,
                                label=phase, budget=self.budget)
        except Exception as exc:                     # noqa: BLE001
            self.breaker.record_failure(f"{type(exc).__name__}: {exc}")
            raise

        self.breaker.record_success()
        print(result)
        self.session.complete(phase, {"summary": result[:4000]})
        return result

    def check_gates(self, phase: str) -> list[str]:
        """What the coordinator verifies for itself, rather than believing.

        A subagent reporting success having written an empty artifact should
        stop the run, not advance it -- and the only way to know is to look.
        """
        problems: list[str] = []

        if self.budget.exceeded():
            problems.append(f"token budget exhausted ({self.budget})")
        if self.breaker.tripped():
            problems.append(
                f"circuit breaker: {self.breaker.consecutive} consecutive "
                f"failures. Last: {self.breaker.last_error}")

        if phase == "gap_analyse":
            path = os.path.join(config.ARTIFACT_DIR, "gap-register.json")
            if not os.path.exists(path):
                problems.append("phase 4 reported success but wrote no gap register")
            else:
                register = GapRegister.load(path)
                problems.extend(register.acceptance_problems())

        if phase == "extract_rules":
            path = os.path.join(config.ARTIFACT_DIR, "rules-ir.json")
            if not os.path.exists(path):
                problems.append("phase 3 reported success but wrote no rules IR")

        return problems

    async def run_all(self, phases: list[str], *, resume: bool) -> None:
        for phase in phases:
            if resume and self.session.is_complete(phase):
                print(f"--- skipping {phase} (already complete)")
                continue

            await self.run_phase(phase)

            problems = self.check_gates(phase)
            if problems:
                print(f"\n!!! HALTED after {phase}:")
                for p in problems:
                    print(f"    - {p}")
                print("\nFix these before continuing. Re-run with --resume when ready.")
                return

        await self.finalize()

    # ----------------------------------------------------------- finalize
    async def finalize(self) -> None:
        print("\n=== FINALIZE " + "=" * 52)
        result = await _run(
            "Call finalize_modernization with confirm_token='ready'. If it "
            "denies, that is the expected outcome: report the briefing it "
            "returned, summarise what the human has to decide, and stop.",
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer, label="finalize", budget=self.budget)
        print(result)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", default="all",
                    help="all, 9a, 9b, finalize, or one phase name")
    ap.add_argument("--resume", action="store_true",
                    help="skip phases already recorded complete")
    ap.add_argument("--approve", action="store_true",
                    help="human approval for finalization. The agent cannot set this.")
    args = ap.parse_args(argv)

    if args.approve:
        # Set in the environment so config -- and therefore the hook -- sees it.
        # The agent has no way to reach this code path.
        os.environ["BH_FINALIZATION_APPROVED"] = "1"
        config.FINALIZATION_APPROVED = True
        print("Finalization APPROVED by the operator.")

    os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
    session = ModernizationSession(config.SESSION_STATE)
    session.load()
    tracer = Tracer(os.path.join(config.ARTIFACT_DIR, "trace.jsonl"))
    run = Modernization(session, tracer)

    if args.phase == "all":
        phases = list(config.PHASES_9A) + list(config.PHASES_9B)
    elif args.phase == "9a":
        phases = list(config.PHASES_9A)
    elif args.phase == "9b":
        # 9B is gated on 9A. Run it against a red 9A and the client ends up
        # guarding around enforcement the backend does not have -- which looks
        # like the rule was migrated and is not.
        missing = [p for p in config.PHASES_9A if not session.is_complete(p)]
        if missing:
            print(f"9B is gated on 9A being green. Not complete: "
                  f"{', '.join(missing)}")
            return 1
        phases = list(config.PHASES_9B)
    elif args.phase == "finalize":
        phases = []
    elif args.phase in PHASE_PROMPTS:
        phases = [args.phase]
    else:
        ap.error(f"unknown phase {args.phase!r}; expected all, 9a, 9b, finalize, "
                 f"or one of {list(PHASE_PROMPTS)}")
        return 2

    # Every phase calls the model. Without a key that surfaces deep inside
    # the SDK transport as a traceback, which reads like a defect in the lab
    # rather than a missing export. Say it here, before any phase starts.
    if not (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
        for line in ("",
                     "ANTHROPIC_API_KEY is not set -- no phase can run.",
                     "    export ANTHROPIC_API_KEY=sk-ant-...       (bash/zsh)",
                     "    $env:ANTHROPIC_API_KEY = 'sk-ant-...'   (PowerShell)",
                     "",
                     "The offline checks need no key and run first:",
                     "    pytest tests/ -q",
                     "    python solution/evaluation/test_suite.py --self-check",
                     ""):
            print(line)
        return 2

    try:
        if phases:
            asyncio.run(run.run_all(phases, resume=args.resume))
        else:
            asyncio.run(run.finalize())
    except KeyboardInterrupt:
        print("\ninterrupted -- session state saved; re-run with --resume")
        return 130

    run.metrics.output_tokens = run.budget.spent
    run.metrics.wall_ms = tracer.total_ms()
    run.metrics.save(os.path.join(config.ARTIFACT_DIR, "metrics.json"))
    print(f"\n{run.budget}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
