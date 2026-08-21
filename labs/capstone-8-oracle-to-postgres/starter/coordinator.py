"""Migration coordinator -- YOU BUILD THIS FILE.

Five phases, in order, each gated on the previous one:

    1 discover   -> inventory the legacy schema
    2 schema     -> Oracle DDL becomes PostgreSQL DDL
    3 data       -> rows move, largest table first
    4 code       -> PL/SQL and application SQL are converted
    5 validate   -> prove equivalence, or say exactly where it broke
    (cutover)    -> human-gated, never automatic

Build order that keeps you unblocked:
    1. hooks.py        -- guardrails first, so nothing you build later can
                          write to the source database by accident
    2. type_mapping.py -- the mechanical mapping table
    3. .claude/agents/ -- the five subagent definitions
    4. this file       -- the orchestration
    5. validation.py   -- the reconciliation checks

Run:  python coordinator.py --migrate-all
      python coordinator.py --phase schema
      python coordinator.py --phase cutover --approve-cutover
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

# TODO(1): Write the coordinator's system prompt.
#
# It has to carry five things, and the last two are the ones people leave
# out:
#   - the five phases, in order, each gated on the previous
#   - "never call a database tool directly, always go through a specialist"
#   - the source is READ-ONLY and it is live production for eleven states
#   - what to do when a specialist REFUSES: queue it for manual review with
#     the reason, and move on
#   - that 80% automated with 20% queued is a success, and 100% automated
#     because it guessed is a failure -- the expensive kind, because nobody
#     finds out until the data is already wrong in production
COORDINATOR_PROMPT = """\
TODO: write the coordinator system prompt
"""

PHASES = ["discover", "schema", "data", "code", "validate"]


def _options(system_prompt: str, model: str, allowed: list[str] | None = None):
    """TODO(2): One place where every SDK knob is set.

    Centralise it so a caller cannot accidentally omit a guardrail.
    Must wire:
      - model, system_prompt, max_turns from config
      - mcp_servers: oracle_src, pg_target, migration_local
      - can_use_tool=hooks.can_use_tool          <- the three PreToolUse guards
      - hooks=[HookMatcher(matcher="*", hooks=[hooks.audit_log])]
    """
    raise NotImplementedError("Build _options")


async def _run(prompt: str, *, system_prompt: str, model: str, tracer: Tracer,
               label: str, budget: hooks.TokenBudget) -> str:
    """TODO(3): Run one agent turn, trace it, and charge the budget.

    Open a `tracer.span(label)`, iterate `query(...)`, collect the text
    from every AssistantMessage block, add the output tokens to the
    budget, and record them on the span.
    """
    raise NotImplementedError("Build _run")


class Migration:
    def __init__(self, session: MigrationSession, tracer: Tracer):
        self.session = session
        self.tracer = tracer
        self.budget = hooks.TokenBudget()
        self.consecutive_failures = 0

    async def discover(self) -> dict:
        """TODO(4): Phase 1. Ask for the inventory, and specifically for
        which columns use Oracle types with no direct PostgreSQL
        equivalent -- by column name, not just by type."""
        raise NotImplementedError

    async def translate_schema(self) -> list[dict]:
        """TODO(5): Phase 2. One schema-translator call per table in
        config.MIGRATION_ORDER. Check self._tripped() between tables."""
        raise NotImplementedError

    async def move_data(self) -> list[dict]:
        """TODO(6): Phase 3. One data-migrator call per table.

        Put the empty-string warning in the PROMPT, not just in the
        subagent definition. The specialist needs it, and so does the
        coordinator that reads the specialist's report.
        """
        raise NotImplementedError

    async def convert_code(self) -> dict:
        """TODO(7): Phase 4. plsql-converter over config.PLSQL_OBJECTS,
        then appsql-rewriter over config.APP_SOURCE_DIR.

        Tell the converter explicitly that PRAGMA AUTONOMOUS_TRANSACTION
        must be REFUSED, not translated.
        """
        raise NotImplementedError

    async def validate(self) -> dict:
        """TODO(8): Phase 5. migration-validator over every table.

        Ask for ucc_debtor.mailing_address_2 by name, and say that it must
        not be folded into an overall pass percentage.
        """
        raise NotImplementedError

    async def cutover(self) -> dict:
        """TODO(9): Attempt pg_cutover.

        Expect the guardrail to deny it. That is the correct outcome, and
        the agent must report the validation state and stop rather than
        looking for a way around the gate.
        """
        raise NotImplementedError

    # ------------------------------------------------------- internals
    def _record(self, result: str) -> None:
        """Given complete."""
        failed = "error" in result.lower() and "no error" not in result.lower()
        self.consecutive_failures = self.consecutive_failures + 1 if failed else 0

    def _tripped(self) -> bool:
        """Given complete. Budget ceiling and circuit breaker."""
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
    """Given complete -- the CLI works as soon as the phases above do."""
    parser = argparse.ArgumentParser(description="Oracle -> PostgreSQL migration agent")
    parser.add_argument("--migrate-all", action="store_true", help="run phases 1-5")
    parser.add_argument("--phase", choices=PHASES + ["cutover"], help="run one phase")
    parser.add_argument("--resume", action="store_true", help="skip completed phases")
    parser.add_argument("--approve-cutover", action="store_true",
                        help="human approval for the irreversible cutover")
    args = parser.parse_args()

    if args.approve_cutover:
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
