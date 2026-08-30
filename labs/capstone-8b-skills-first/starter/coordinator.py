"""Migration coordinator -- skills-first.

Same five phases as the subagent build, same schema, same defects, same
evaluation set. One structural difference:

    Capstone 8   coordinator -> 5 subagents, each with its own context
    Capstone 8B  one context, loading 5 skills on demand

Run everything:      python coordinator.py --migrate-all
Run one phase:       python coordinator.py --phase schema
List the skill map:  python coordinator.py --list-skills
Cutover:             python coordinator.py --phase cutover --approve-cutover
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, HookMatcher, query

import config
import hooks
from observability.tracer import Tracer
from report import render_console, write_html_report, write_json_report
from session import MigrationSession
from tools_local import local_server
from tools_oracle import oracle_server
from tools_postgres import pg_server

# TODO(1): the coordinator system prompt.
#
# Start from the five phases and the non-negotiable rules. Then add the two
# instructions that are specific to THIS architecture and have no equivalent
# in the subagent build:
#
#   a. Skills are not documentation the agent may consult if it feels like
#      it. Say what they are instead, and what the agent should do when a
#      skill bundles a script that computes an answer the agent could also
#      reason out. (Hint: the script is unit-tested and the reasoning is not.)
#
#   b. In phase 5 the agent audits work it did itself, earlier in the same
#      conversation. Write the instruction that compensates. Something
#      checkable, not "be objective".
COORDINATOR_PROMPT = ""

PHASES = ["discover", "schema", "data", "code", "validate"]

# TODO(2): which skills each phase may load.
#
# This is the skills-first analogue of the `tools:` line in a subagent's
# frontmatter, and it does the same job: a phase cannot reach knowledge it has
# no business using.
#
# Fill in the five phases. Three constraints to reason through:
#
#   - `discover` needs no rulebook at all. Leave it empty and be sure you can
#     say why that is not laziness.
#   - the load phase must NOT be able to load the validation skill. Work out
#     what goes wrong if it can.
#   - exactly one skill belongs to TWO phases. Finding it is the exercise:
#     it is the piece of knowledge that both the phase doing the work and the
#     phase checking the work have to agree on. In the subagent build it was
#     copy-pasted into two prompts and the copies were free to drift.
#
# `tests/test_skills_wellformed.py` asserts that every skill here exists, that
# every skill on disk is used by some phase, and which phases share the shared
# one. Run it once you have filled this in.
PHASE_SKILLS: dict[str, list[str]] = {
    "discover": [],
    "schema":   [],
    "data":     [],
    "code":     [],
    "validate": [],
    "cutover":  [],
}


def _options(system_prompt: str, model: str, skills: list[str],
             allowed: list[str] | None = None):
    """One place where every SDK knob is set, so the guardrails cannot be
    accidentally omitted by a caller that forgot one."""
    return ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        max_turns=config.MAX_TURNS,
        mcp_servers={
            "oracle_src": oracle_server,
            "pg_target": pg_server,
            "migration_local": local_server,
        },
        allowed_tools=allowed,
        can_use_tool=hooks.can_use_tool,
        hooks={"PostToolUse": [HookMatcher(matcher="*", hooks=[hooks.audit_log])]},
        # TODO(3): two options make skills work, and BOTH are required.
        #
        # One tells the SDK to read filesystem settings from the project --
        # without it `.claude/skills/` is never opened. Find it in
        # `ClaudeAgentOptions`; it takes a list of scopes.
        #
        # The other selects which of the discovered skills this call may use.
        # Check its type before you guess: one of the accepted values means
        # "every skill, every phase", which would throw away the scoping you
        # designed in TODO(2).
        #
        # This is the failure worth understanding: if you omit these, nothing
        # errors. No warning, no missing-skill message. The agent simply
        # improvises the type mapping from memory and produces a migration
        # that looks fine and is not. Before moving on, run one phase and
        # prove from `migration_audit.jsonl` that a skill script was actually
        # executed.
    )


async def _run(prompt: str, *, system_prompt: str, model: str, tracer: Tracer,
               label: str, budget: hooks.TokenBudget, skills: list[str]) -> str:
    """Run one agent turn, trace it, and charge the budget."""
    # TODO(4): iterate the query, collect AssistantMessage text, charge the
    # token budget from the final usage, and record the span.
    raise NotImplementedError("Build _run")


class Migration:
    def __init__(self, session: MigrationSession, tracer: Tracer):
        self.session = session
        self.tracer = tracer
        self.budget = hooks.TokenBudget()
        self.consecutive_failures = 0

    async def _turn(self, prompt: str, *, label: str, phase: str) -> str:
        """One agent turn, with this phase's skills."""
        # TODO(5): delegate to _run, passing PHASE_SKILLS[phase].
        raise NotImplementedError("Build _turn")

    # ---------------------------------------------------------- phases
    async def discover(self) -> dict:
        # TODO(6): one call to oracle_describe_schema, then summarise the
        # inventory. Ask for specifics -- name the columns whose types have no
        # direct equivalent, not just the type names.
        raise NotImplementedError("Build discover")

    async def translate_schema(self) -> list[dict]:
        # TODO(7): one table at a time, in config.MIGRATION_ORDER.
        # Tell the agent to run the skill's checker BEFORE reasoning, and to
        # resolve every column it flags by reading real rows.
        raise NotImplementedError("Build translate_schema")

    async def move_data(self) -> list[dict]:
        # TODO(8): one table at a time, largest first.
        #
        # Resist putting the null_as rule in this prompt. It belongs in the
        # skill, which phase 5 also reads -- that shared file is the whole
        # argument for this architecture, and duplicating the rule here
        # quietly gives it up.
        raise NotImplementedError("Build move_data")

    async def convert_code(self) -> dict:
        # TODO(9): every object in config.PLSQL_OBJECTS, then the application
        # source. Instruct the agent to scan before converting, and to write a
        # MANUAL_REVIEW.md rather than a conversion when the scanner refuses.
        raise NotImplementedError("Build convert_code")

    async def validate(self) -> dict:
        # TODO(10): all six checks, every table.
        #
        # This prompt needs a sentence the subagent build does not: the agent
        # performed the load itself, earlier in this same context. Say what
        # follows from that concretely.
        raise NotImplementedError("Build validate")

    async def cutover(self) -> dict:
        # TODO(11): attempt pg_cutover and report the denial when it comes.
        # The agent must not try to work around the gate -- and you should
        # verify it does not, rather than trusting the instruction.
        raise NotImplementedError("Build cutover")

    # ------------------------------------------------------- internals
    def _record(self, result: str) -> None:
        failed = "error" in result.lower() and "no error" not in result.lower()
        self.consecutive_failures = self.consecutive_failures + 1 if failed else 0

    def _tripped(self) -> bool:
        if self.budget.exceeded():
            print(f"\n!! TOKEN BUDGET EXHAUSTED ({self.budget}) -- halting.")
            return True
        if self.consecutive_failures >= config.CIRCUIT_BREAKER_THRESHOLD:
            print(
                f"\n!! CIRCUIT BREAKER: {self.consecutive_failures} consecutive "
                f"failures -- halting rather than burning budget on a broken "
                f"pipeline."
            )
            return True
        return False


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Oracle -> PostgreSQL migration agent (skills-first)")
    parser.add_argument("--migrate-all", action="store_true", help="run phases 1-5")
    parser.add_argument("--phase", choices=PHASES + ["cutover"], help="run one phase")
    parser.add_argument("--resume", action="store_true", help="skip completed phases")
    parser.add_argument("--approve-cutover", action="store_true",
                        help="human approval for the irreversible cutover")
    parser.add_argument("--list-skills", action="store_true",
                        help="print the phase -> skills map and exit")
    args = parser.parse_args()

    if args.list_skills:
        for phase in PHASES + ["cutover"]:
            loaded = ", ".join(PHASE_SKILLS[phase]) or "(none)"
            print(f"{phase:<10} {loaded}")
        return 0

    if args.approve_cutover:
        # Set for this process only. The agent has no way to do this.
        os.environ["CUTOVER_APPROVED"] = "1"
        config.CUTOVER_APPROVED = True

    if not args.migrate_all and not args.phase:
        parser.print_help()
        return 2

    os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
    session = MigrationSession(config.SESSION_STATE)
    if args.resume:
        session.load()
        print(f"Resuming. Already complete: {session.completed_phases() or 'nothing'}")

    tracer = Tracer()
    migration = Migration(session, tracer)

    handlers = {
        "discover": migration.discover,
        "schema": migration.translate_schema,
        "data": migration.move_data,
        "code": migration.convert_code,
        "validate": migration.validate,
        "cutover": migration.cutover,
    }

    try:
        if args.phase:
            await handlers[args.phase]()
        else:
            for phase in PHASES:
                if args.resume and session.is_complete(phase):
                    print(f"--- skipping {phase} (already complete)")
                    continue
                await handlers[phase]()
                if migration._tripped():
                    break
    except KeyboardInterrupt:
        print("\nInterrupted. State saved -- re-run with --resume to continue.")
        return 130
    finally:
        session.save()
        spans = tracer.finish()
        render_console(spans, migration.budget)
        write_json_report(spans, migration.budget, config.ARTIFACT_DIR)
        write_html_report(spans, migration.budget, config.ARTIFACT_DIR)

    print(f"\nToken usage: {migration.budget}")
    print(f"Reports: {config.ARTIFACT_DIR}/migration_report.html")
    print(f"Audit log: {config.AUDIT_LOG}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
