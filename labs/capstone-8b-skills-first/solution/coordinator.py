"""Migration coordinator -- skills-first.

Same five phases as the subagent build, same schema, same defects, same
evaluation set. One structural difference:

    Capstone 8   coordinator -> 5 subagents, each with its own context
    Capstone 8B  one context, loading 5 skills on demand

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
2. TRANSLATE SCHEMA - one table at a time. The oracle-pg-typing skill
   carries the mapping rules and a deterministic checker.
3. MOVE DATA - one table at a time, largest first, so a capacity or
   encoding problem surfaces early.
4. CONVERT CODE - every PL/SQL object, then the application source.
5. VALIDATE - all six checks, every table. Only after it reports may you
   propose pg_cutover.

You have skills available. They are not documentation you may consult --
they are the procedure. When a skill is loaded for a phase, follow it.
Run the checker scripts it bundles rather than reasoning out an answer
the script can compute: the script is faster, it is consistent on a bad
day, and it is unit-tested.

Rules that are not negotiable:

- When an object cannot be converted automatically, put it on the
  manual-review queue with the specific reason and move on. Do not invent
  a translation you are not confident in.
- A migration that reports 80% automated and 20% needing review is a
  success. A migration that reports 100% automated because you guessed
  is a failure, and it is the expensive kind of failure, because nobody
  finds out until the data is already wrong in production.
- In phase 5 you are auditing your own work from phases 2-4. Re-derive
  every number from the database. Do not report a count you remember
  writing.
- You cannot approve your own cutover. When validation is done, report
  the numbers and stop.
"""

PHASES = ["discover", "schema", "data", "code", "validate"]

# Which skills each phase may load.
#
# This is the skills-first analogue of the `tools:` line in a subagent's
# frontmatter, and it does the same job: a phase cannot reach knowledge it
# has no business using. Phase 3 gets the loading rules but not the
# validation procedure, so it cannot mark its own work correct.
#
# `nullability-preservation` appears TWICE on purpose. In the subagent build
# that knowledge was copy-pasted into two agent prompts, and the copies were
# free to drift. Here the loader and the validator read the same file, so
# they cannot disagree about what a correct load looks like. That single
# shared file is the clearest argument for this architecture.
PHASE_SKILLS: dict[str, list[str]] = {
    "discover": [],
    "schema":   ["oracle-pg-typing"],
    "data":     ["nullability-preservation"],
    "code":     ["plsql-conversion", "appsql-rewriting"],
    "validate": ["migration-validation", "nullability-preservation"],
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
        # Without this, `.claude/skills/` is never read and every skill
        # silently does not exist. The agent then improvises the type
        # mapping from memory and the run looks like it worked.
        setting_sources=["project"],
        # Per-phase allowlist. `None` would mean "no skills"; `"all"` would
        # mean every discovered skill in every phase, which defeats the
        # scoping this architecture depends on.
        skills=skills,
    )


async def _run(prompt: str, *, system_prompt: str, model: str, tracer: Tracer,
               label: str, budget: hooks.TokenBudget, skills: list[str]) -> str:
    """Run one agent turn, trace it, and charge the budget."""
    chunks: list[str] = []
    message = None
    with tracer.span(label) as span:
        async for message in query(
            prompt=prompt,
            options=_options(system_prompt, model, skills),
        ):
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

    async def _turn(self, prompt: str, *, label: str, phase: str) -> str:
        return await _run(
            prompt,
            system_prompt=COORDINATOR_PROMPT,
            model=config.COORDINATOR_MODEL,
            tracer=self.tracer,
            label=label,
            budget=self.budget,
            skills=PHASE_SKILLS[phase],
        )

    # ---------------------------------------------------------- phases
    async def discover(self) -> dict:
        print("\n=== PHASE 1 / 5  DISCOVER " + "=" * 40)
        print("    skills: (none -- inventory needs no rulebook)")
        result = await self._turn(
            "Call oracle_describe_schema for the MERIDIAN schema. Summarise "
            "the inventory: how many tables, how many rows in total, which "
            "PL/SQL objects exist, and which columns use Oracle types that "
            "have no direct PostgreSQL equivalent. Be specific about the "
            "types -- name the column, not just the type.",
            label="discover", phase="discover",
        )
        print(result)
        self.session.complete("discover", {"summary": result[:4000]})
        return {"summary": result}

    async def translate_schema(self) -> list[dict]:
        print("\n=== PHASE 2 / 5  TRANSLATE SCHEMA " + "=" * 32)
        print(f"    skills: {', '.join(PHASE_SKILLS['schema'])}")
        out = []
        for table in config.MIGRATION_ORDER:
            if self._tripped():
                break
            print(f"  -> {table}")
            result = await self._turn(
                f"Translate the Oracle table {table} into PostgreSQL 16 DDL.\n\n"
                f"Follow the oracle-pg-typing skill. Run its check_mapping.py "
                f"script on the DDL first, then read 20 real rows and resolve "
                f"every column it marked check_data or manual.\n\n"
                f"Requirements:\n"
                f"- Create everything in the {config.POSTGRES.target_schema} schema.\n"
                f"- Do not quote identifiers.\n"
                f"- Write the DDL to artifacts/ddl/{table.lower()}.sql and the "
                f"decision log to artifacts/decisions/{table.lower()}.md, then "
                f"apply it with pg_apply_ddl.",
                label=f"schema:{table}", phase="schema",
            )
            out.append({"table": table, "result": result})
            self._record(result)
        self.session.complete("schema", {"tables": [o["table"] for o in out]})
        return out

    async def move_data(self) -> list[dict]:
        print("\n=== PHASE 3 / 5  MOVE DATA " + "=" * 39)
        print(f"    skills: {', '.join(PHASE_SKILLS['data'])}")
        out = []
        for table in config.MIGRATION_ORDER:
            if self._tripped():
                break
            print(f"  -> {table}")
            result = await self._turn(
                f"Move {table} from Oracle to PostgreSQL in batches of "
                f"{config.BATCH_SIZE}.\n\n"
                f"Follow the nullability-preservation skill. It states the "
                f"load-side rule that decides whether this migration is "
                f"correct.\n\n"
                f"Report rows read from Oracle and rows landed in PostgreSQL.",
                label=f"data:{table}", phase="data",
            )
            out.append({"table": table, "result": result})
            self._record(result)
        self.session.complete("data", {"tables": [o["table"] for o in out]})
        return out

    async def convert_code(self) -> dict:
        print("\n=== PHASE 4 / 5  CONVERT CODE " + "=" * 36)
        print(f"    skills: {', '.join(PHASE_SKILLS['code'])}")
        plsql = []
        for obj in config.PLSQL_OBJECTS:
            if self._tripped():
                break
            print(f"  -> PL/SQL {obj}")
            result = await self._turn(
                f"Convert {obj} to PL/pgSQL.\n\n"
                f"Follow the plsql-conversion skill. Run its scanner on the "
                f"source BEFORE converting: if any construct comes back "
                f"marked REFUSE, write a MANUAL_REVIEW.md instead of a "
                f"conversion and move on.\n\n"
                f"Write the result to artifacts/plsql/{obj.lower()}.sql, or "
                f"artifacts/plsql/{obj.lower()}.MANUAL_REVIEW.md if refused.",
                label=f"plsql:{obj}", phase="code",
            )
            plsql.append({"object": obj, "result": result})
            self._record(result)

        print("  -> application SQL")
        appsql = await self._turn(
            f"Rewrite the Oracle SQL in {config.APP_SOURCE_DIR} for PostgreSQL.\n\n"
            f"Follow the appsql-rewriting skill. Run its find_oracleisms.py "
            f"scanner over the directory first, then produce one unified diff "
            f"per file at artifacts/appsql/<filename>.diff. Never edit an "
            f"original.\n\n"
            f"Pay particular attention to debtors_missing_address_line_2 in "
            f"filing_repository.py -- explain in the diff comment why that "
            f"query's behaviour depends on how the data was loaded, not just "
            f"on how the SQL is written.",
            label="appsql", phase="code",
        )
        self.session.complete("code", {"plsql": [p["object"] for p in plsql]})
        return {"plsql": plsql, "appsql": appsql}

    async def validate(self) -> dict:
        print("\n=== PHASE 5 / 5  VALIDATE " + "=" * 40)
        print(f"    skills: {', '.join(PHASE_SKILLS['validate'])}")
        print("    NOTE: this phase audits work done earlier in THIS context.")
        result = await self._turn(
            "Validate the migration.\n\n"
            "Follow the migration-validation skill. Run all six checks for "
            f"every table in {config.MIGRATION_ORDER}.\n\n"
            "You performed the load yourself earlier in this conversation. "
            "That makes you the wrong person to take your own word for it, so "
            "re-derive every number with a query. Do not report a count you "
            "remember writing.\n\n"
            "Write artifacts/validation_summary.json with keys "
            "tables_validated, checks_passed, checks_failed, and defects[].",
            label="validate", phase="validate",
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
        result = await self._turn(
            "Attempt pg_cutover with the confirm token from CUTOVER_TOKEN. "
            "If the guardrail denies it, report the validation state and stop. "
            "Do not attempt to work around the gate.",
            label="cutover", phase="cutover",
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
