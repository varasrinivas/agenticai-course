"""Migration coordinator.

Five phases, in order, each gated on the previous one:

    1 discover   -> inventory the legacy schema
    2 schema     -> Oracle DDL becomes PostgreSQL DDL
    3 data       -> rows move, largest table first
    4 code       -> PL/SQL and application SQL are converted
    5 validate   -> prove equivalence, or say exactly where it broke
    (cutover)    -> human-gated, never automatic

Run everything:      python coordinator.py --migrate-all
Run one phase:       python coordinator.py --phase schema
Resume after a stop: python coordinator.py --migrate-all --resume
Cutover:             python coordinator.py --phase cutover --approve-cutover
"""

from __future__ import annotations

import argparse
import asyncio
import json
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

COORDINATOR_PROMPT = """\
You are the migration coordinator for an Oracle-to-PostgreSQL database
migration at Meridian Public Records. The source is a live UCC filing
system for eleven Secretary of State offices. It is READ-ONLY.

Work in five phases, in order. Do not start a phase until the previous
one has reported success.

1. DISCOVER  - call oracle_describe_schema once. Build an inventory of
   every table, sequence, trigger, view, materialized view, package,
   procedure and function.
2. TRANSLATE SCHEMA - delegate each table to the schema-translator
   subagent. Collect the generated DDL and the type-mapping decision log.
3. MOVE DATA - delegate each table to the data-migrator subagent,
   largest first, so a capacity or encoding problem surfaces early.
4. CONVERT CODE - delegate every PL/SQL object to plsql-converter and
   every application file to appsql-rewriter.
5. VALIDATE - delegate to migration-validator. Only after it reports may
   you propose pg_cutover.

Rules that are not negotiable:

- Never call a database tool directly. Always go through a specialist.
- When a specialist reports that an object cannot be converted
  automatically, put it on the manual-review queue with the specific
  reason and move on. Do not invent a translation you are not confident
  in.
- A migration that reports 80% automated and 20% needing review is a
  success. A migration that reports 100% automated because you guessed
  is a failure, and it is the expensive kind of failure, because nobody
  finds out until the data is already wrong in production.
- You cannot approve your own cutover. When validation is done, report
  the numbers and stop.
"""

PHASES = ["discover", "schema", "data", "code", "validate"]


def _options(system_prompt: str, model: str, allowed: list[str] | None = None):
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
        hooks=[HookMatcher(matcher="*", hooks=[hooks.audit_log])],
    )


async def _run(prompt: str, *, system_prompt: str, model: str, tracer: Tracer,
               label: str, budget: hooks.TokenBudget) -> str:
    """Run one agent turn, trace it, and charge the budget."""
    chunks: list[str] = []
    with tracer.span(label) as span:
        async for message in query(prompt=prompt, options=_options(system_prompt, model)):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    text = getattr(block, "text", None)
                    if text:
                        chunks.append(text)
        usage = getattr(message, "usage", None)
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        budget.add(output_tokens)
        span.tokens = output_tokens
    return "\n".join(chunks)


class Migration:
    def __init__(self, session: MigrationSession, tracer: Tracer):
        self.session = session
        self.tracer = tracer
        self.budget = hooks.TokenBudget()
        self.consecutive_failures = 0

    # ---------------------------------------------------------- phases
    async def discover(self) -> dict:
        print("\n=== PHASE 1 / 5  DISCOVER " + "=" * 40)
        result = await _run(
            "Call oracle_describe_schema for the MERIDIAN schema. Summarise "
            "the inventory: how many tables, how many rows in total, which "
            "PL/SQL objects exist, and which columns use Oracle types that "
            "have no direct PostgreSQL equivalent. Be specific about the "
            "types -- name the column, not just the type.",
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer,
            label="discover",
            budget=self.budget,
        )
        print(result)
        self.session.complete("discover", {"summary": result[:4000]})
        return {"summary": result}

    async def translate_schema(self) -> list[dict]:
        print("\n=== PHASE 2 / 5  TRANSLATE SCHEMA " + "=" * 32)
        out = []
        for table in config.MIGRATION_ORDER:
            if self._tripped():
                break
            print(f"  -> {table}")
            result = await _run(
                f"Use the schema-translator subagent to translate the Oracle "
                f"table {table} into PostgreSQL 16 DDL.\n\n"
                f"Requirements:\n"
                f"- Map Oracle DATE to timestamp(0), NOT date. Say why in the "
                f"decision log.\n"
                f"- Replace any sequence + BEFORE INSERT trigger identity "
                f"pattern with GENERATED BY DEFAULT AS IDENTITY, and emit a "
                f"setval-equivalent for after the data load.\n"
                f"- Do not quote identifiers.\n"
                f"- Create everything in the {config.POSTGRES.target_schema} schema.\n"
                f"- Write the DDL to artifacts/ddl/{table.lower()}.sql and the "
                f"decision log to artifacts/decisions/{table.lower()}.md, then "
                f"apply it with pg_apply_ddl.",
                system_prompt=COORDINATOR_PROMPT,
                model=config.COORDINATOR_MODEL,
                tracer=self.tracer,
                label=f"schema:{table}",
                budget=self.budget,
            )
            out.append({"table": table, "result": result})
            self._record(result)
        self.session.complete("schema", {"tables": [o["table"] for o in out]})
        return out

    async def move_data(self) -> list[dict]:
        print("\n=== PHASE 3 / 5  MOVE DATA " + "=" * 39)
        out = []
        for table in config.MIGRATION_ORDER:
            if self._tripped():
                break
            print(f"  -> {table}")
            result = await _run(
                f"Use the data-migrator subagent to move {table} from Oracle to "
                f"PostgreSQL in batches of {config.BATCH_SIZE}.\n\n"
                f"Critical: set null_as explicitly on pg_copy_load. Oracle "
                f"stores the empty string as NULL. If those values arrive in "
                f"PostgreSQL as zero-length strings instead of NULL, every "
                f"IS NULL predicate in the application silently starts "
                f"matching fewer rows -- nothing errors, the numbers just "
                f"quietly go wrong. Handle CLOB and BLOB columns out of band "
                f"rather than inline in the CSV.\n"
                f"Report rows read from Oracle and rows landed in PostgreSQL.",
                system_prompt=COORDINATOR_PROMPT,
                model=config.COORDINATOR_MODEL,
                tracer=self.tracer,
                label=f"data:{table}",
                budget=self.budget,
            )
            out.append({"table": table, "result": result})
            self._record(result)
        self.session.complete("data", {"tables": [o["table"] for o in out]})
        return out

    async def convert_code(self) -> dict:
        print("\n=== PHASE 4 / 5  CONVERT CODE " + "=" * 36)
        plsql = []
        for obj in config.PLSQL_OBJECTS:
            if self._tripped():
                break
            print(f"  -> PL/SQL {obj}")
            result = await _run(
                f"Use the plsql-converter subagent on {obj}.\n\n"
                f"Packages have no PostgreSQL equivalent -- convert a package "
                f"to a schema of the same name containing one function per "
                f"public routine.\n"
                f"If the object uses PRAGMA AUTONOMOUS_TRANSACTION, REFUSE to "
                f"convert it and queue it for manual review. Dropping the "
                f"pragma would change the semantics: audit rows would start "
                f"disappearing on rollback, which is the opposite of what an "
                f"audit log is for.\n"
                f"Write the result to artifacts/plsql/{obj.lower()}.sql.",
                system_prompt=COORDINATOR_PROMPT,
                model=config.COORDINATOR_MODEL,
                tracer=self.tracer,
                label=f"plsql:{obj}",
                budget=self.budget,
            )
            plsql.append({"object": obj, "result": result})
            self._record(result)

        print("  -> application SQL")
        appsql = await _run(
            f"Use the appsql-rewriter subagent. Scan {config.APP_SOURCE_DIR} "
            f"with scan_app_sql, then for each file produce a PostgreSQL "
            f"rewrite as a unified diff written to "
            f"artifacts/appsql/<filename>.diff. Never edit the original.\n"
            f"Pay particular attention to debtors_missing_address_line_2 in "
            f"filing_repository.py -- explain in the diff comment why that "
            f"query's behaviour depends on how the data was loaded, not just "
            f"on how the SQL is written.",
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer,
            label="appsql",
            budget=self.budget,
        )
        self.session.complete("code", {"plsql": [p["object"] for p in plsql]})
        return {"plsql": plsql, "appsql": appsql}

    async def validate(self) -> dict:
        print("\n=== PHASE 5 / 5  VALIDATE " + "=" * 40)
        result = await _run(
            "Use the migration-validator subagent. For every table in "
            f"{config.MIGRATION_ORDER}, run all six checks: row count, "
            "column checksum, per-column NULL count, per-column "
            "empty-string count (PostgreSQL only), foreign-key integrity, "
            "and a 20-row spot-check diff.\n\n"
            "Report ucc_debtor.mailing_address_2 explicitly. In Oracle that "
            "column is NULL for roughly 1,400 rows. If PostgreSQL reports a "
            "non-zero empty-string count for it, the load is defective and "
            "you must say so plainly -- do not average it away into an "
            "overall pass rate.\n\n"
            "Write artifacts/validation_summary.json with keys "
            "tables_validated, checks_passed, checks_failed, and defects[].",
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer,
            label="validate",
            budget=self.budget,
        )
        print(result)
        self.session.complete("validate", {"summary": result[:4000]})
        return {"summary": result}

    async def cutover(self) -> dict:
        print("\n=== CUTOVER " + "=" * 54)
        if not config.CUTOVER_APPROVED:
            print(
                "Cutover is human-gated. Read artifacts/validation_report.html, "
                "then re-run with --approve-cutover."
            )
        result = await _run(
            "Attempt pg_cutover with the confirm token from CUTOVER_TOKEN. "
            "If the guardrail denies it, report the validation state and stop. "
            "Do not attempt to work around the gate.",
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer,
            label="cutover",
            budget=self.budget,
        )
        print(result)
        return {"summary": result}

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
    parser = argparse.ArgumentParser(description="Oracle -> PostgreSQL migration agent")
    parser.add_argument("--migrate-all", action="store_true", help="run phases 1-5")
    parser.add_argument("--phase", choices=PHASES + ["cutover"], help="run one phase")
    parser.add_argument("--resume", action="store_true", help="skip completed phases")
    parser.add_argument("--approve-cutover", action="store_true",
                        help="human approval for the irreversible cutover")
    args = parser.parse_args()

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
