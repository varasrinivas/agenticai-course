# CAPSTONE-8B — Legacy Migration Agent, Skills-First

**Difficulty: 5/5 · 8–10 hours · SDK Tier 3 (`claude-agent-sdk`, spec-driven)**

Build the Oracle → PostgreSQL migration agent again — the same schema, the same planted defects,
the same 20 evaluation cases — with **Agent Skills instead of subagents**. Then measure which
architecture actually did better and write down the answer, including when the answer is
unflattering.

> **Do Capstone 8 first.** This lab is a comparison, and a comparison needs something to compare
> against. If you have not built the subagent version, build that one.

---

## The one-sentence version

Three of Capstone 8's five subagents were not really delegation — they were rulebooks with a
context window attached. This lab takes the rulebooks out, ships them as skills, and finds out
what that costs and what it buys.

---

## What actually changes

| | Capstone 8 | Capstone 8B |
|---|---|---|
| Specialist knowledge | 5 subagent prompts | 5 skills with `references/` + `scripts/` |
| Contexts | 6 (coordinator + 5) | 1 |
| Model routing | Sonnet / Haiku per specialist | one model |
| `scan_app_sql` | MCP tool | skill-bundled script |
| Shared knowledge | copy-pasted into 2 prompts | **one file, loaded by 2 phases** |
| Hooks, guardrails, HITL gate | — | **byte-identical** |
| Tests, evaluation set | — | same, plus `test_skills_wellformed.py` |

The last two rows matter as much as the first. Guardrails sit between the agent and its tools, so
reorganising the agent's knowledge does not touch them. **That is a result, not an omission.**

---

## The thing this lab is actually testing

In Capstone 8, `migration-validator` ran in its own context. It had never seen the type mappings
chosen in phase 2 or the load decisions made in phase 3. When it said "all clear", that was an
independent opinion.

Here, phase 5 runs in the same context that did the work. **It is auditing itself.**

`evaluation/architecture_comparison.md` is where you measure whether that matters. Break the load
on purpose, run validation three times, and record whether the validator caught its own mistake.

If it does worse than the subagent version, **write that down**. A comparison that flatters the
newer architecture is worth nothing to whoever reads it deciding what to build.

---

## Layout

```
capstone-8b-skills-first/
├── spec/agent-spec.md          the canonical spec -- read next to Capstone 8's
├── legacy-oracle/              IDENTICAL to Capstone 8: same schema, same planted defects
├── app/                        IDENTICAL: same rewrite targets
├── starter/                    your workspace -- SKILL.md files and scripts are TODO
├── solution/                   the reference build
├── tests/                      pytest -- same suite, plus test_skills_wellformed.py
├── expected_output/            what a good run looks like
├── deploy/                     local / GCP / AWS
└── appendix/manual-loop.py     the raw-API version, for contrast only
```

The fixtures are byte-identical to Capstone 8 on purpose. If they drift, the comparison stops
meaning anything.

---

## The five skills

| Skill | Was | Loaded by |
|---|---|---|
| `oracle-pg-typing` | `schema-translator` + `type_mapping.py` | schema |
| `plsql-conversion` | `plsql-converter` | code |
| `appsql-rewriting` | `appsql-rewriter` + `oracle_constructs.py` + `scan_app_sql` | code |
| `nullability-preservation` | duplicated in `data-migrator` **and** `migration-validator` | **data + validate** |
| `migration-validation` | `migration-validator` + `validation.py` | validate |

`nullability-preservation` is the interesting row. In Capstone 8 the empty-string rule lived in
two subagent prompts, free to drift apart. Here the phase that loads the data and the phase that
checks the load read the same file, so they cannot disagree about what "correct" means.

`plsql-conversion` ships no scanner of its own — it calls `appsql-rewriting`'s. One catalog, two
consumers.

---

## Getting started

```bash
cp starter/.env.example starter/.env      # add your ANTHROPIC_API_KEY
pip install -r requirements.txt

docker compose -f starter/docker-compose.yml up -d
# WAIT. Oracle takes 1-3 minutes on first boot.
# It must read "healthy", not just "running":
docker compose -f starter/docker-compose.yml ps
```

Then work through the TODOs. Suggested order:

1. `.claude/skills/*/scripts/*.py` — the checkers. They are pure Python, unit-tested, and need
   no API key. Running them over `legacy-oracle/` is also how you *find* what the skills need
   to say.
2. `.claude/skills/*/SKILL.md` and `references/` — the procedures, informed by step 1.
3. `coordinator.py` — the `PHASE_SKILLS` map and the two `ClaudeAgentOptions` fields that make
   skill discovery work.
4. `hooks.py`, `tools_local.py` — the guardrails.

```bash
pytest tests/ -v                       # grades solution/ by default
TEST_TARGET=starter pytest tests/ -v   # grades your work
```

Against a fresh starter, `test_skills_wellformed.py` gives you 39 passes and 6 failures. The 6
are your work list.

---

## Running it

```bash
cd starter
python coordinator.py --list-skills    # sanity-check the phase map first
python coordinator.py --migrate-all
python coordinator.py --phase validate
```

Cutover is human-gated and will be denied:

```bash
python coordinator.py --phase cutover                     # denied, as designed
python coordinator.py --phase cutover --approve-cutover   # only a human can do this
```

---

## Two things that will bite you

**A skill that does not load fails silently.** No error, no warning. The agent improvises the
type mapping from memory and the run looks fine. Both `setting_sources` and `skills` must be set
on `ClaudeAgentOptions`. Before trusting any green run:

```bash
grep -c "check_mapping" migration_audit.jsonl    # must be > 0
```

**Your first validation run is supposed to fail.** Nothing yet forces `null_as` on the load, so
check 4 on `ucc_debtor.mailing_address_2` comes back red — 1,412 Oracle NULLs arriving as empty
strings. Fix it in `nullability-preservation/SKILL.md`, re-run phase 3, re-validate.

If your **first** run comes back clean, do not celebrate. Check the validator actually ran — an
empty defect list and a validator that never executed look identical in the JSON. In this
architecture that is the failure mode to watch hardest, because the validator has every reason to
believe its own earlier work.

---

## Done when

- [ ] `pytest tests/ -v` passes against `starter/`
- [ ] `python evaluation/test_suite.py` scores ≥ 18/20
- [ ] `docker compose up` runs phases 1–5 unattended and **stops** at the cutover gate
- [ ] `ucc_debtor.mailing_address_2` has 1,412 NULLs and 0 empty strings
- [ ] `migration_audit.jsonl` has one entry per tool call and no credentials
- [ ] Oracle writes are denied and logged
- [ ] `evaluation/architecture_comparison.md` is filled in from **your** run, including the
      validator-independence trials — and says so plainly if 8B came out worse
