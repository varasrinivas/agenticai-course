# Architecture comparison — subagents vs skills

**This file is a deliverable, not a worksheet.** It is the reason Capstone 8B exists as a
separate lab rather than a refactor of Capstone 8. Two architectures, one problem, one
evaluation set — and a measured answer instead of an opinion.

Fill in the right-hand column from **your own run**. Do not copy the baseline across.

---

## Rules for filling this in

1. **Run the migration end to end at least twice.** The first run is expected to fail the NULL
   check; that failure is data, not a mistake to hide.
2. **Take every number from an artifact**, not from the console scrollback:
   `artifacts/migration_report.json`, `artifacts/validation_summary.json`,
   `migration_audit.jsonl`.
3. **If 8B does worse, write down that it did worse.** A comparison that flatters the newer
   architecture is worth nothing to the person who reads it deciding what to build. The honest
   result is the deliverable; a favourable result is not the goal.

---

## 1. Cost and time

Baseline from Capstone 8's `expected_output/migration_report.json` — a clean second run, after
the empty-string defect was fixed.

| Measure | Capstone 8 (subagents) | Capstone 8B (skills) | Source |
|---|---:|---:|---|
| Total output tokens | 118,940 | | `migration_report.json` → `total_output_tokens` |
| Wall clock | 279.4 s | | `total_ms` |
| Estimated cost | $1.78 | | `estimated_usd` |
| Spans | 19 | | `spans` |
| Errors | 0 | | `errors` |

### Per phase

| Phase | C8 tokens | C8 ms | 8B tokens | 8B ms |
|---|---:|---:|---:|---:|
| discover | 3,204 | 8,242 | | |
| schema (6 tables) | 41,880 | 71,403 | | |
| data (6 tables) | 11,120 | 88,205 | | |
| plsql (4 objects) | 38,192 | 62,703 | | |
| appsql | 14,903 | 26,512 | | |
| validate | 9,641 | 22,349 | | |

**Predict before you measure, then check yourself.** Write your prediction here first:

- Which phases should get *cheaper* under skills, and why?
- Which should get *more expensive*, and why?
- What happens to `schema`, which runs six times and reloads the same rulebook each time?

> Prediction: _______________________________________________
>
> Actual: ___________________________________________________
>
> Where you were wrong, and why: ____________________________

---

## 2. Correctness — the part that matters

Both architectures run the same 20 evaluation cases and face the same planted defects.

| Measure | Capstone 8 | Capstone 8B | Source |
|---|---:|---:|---|
| Evaluation score (of 20) | | | `python evaluation/test_suite.py` |
| Tables validated | 6 | | `validation_summary.json` |
| Checks passed | 36 | | `validation_summary.json` |
| Checks failed (2nd run) | 0 | | `validation_summary.json` |
| Manual-review items | 3 | | `migration_report.json` → `manual_review_queue` |

Capstone 8's three manual-review items, for comparison. **A migration that queues fewer is not
doing better** — it is either finding less or guessing more:

1. `PKG_FILING_MAINT.log_audit` — `PRAGMA AUTONOMOUS_TRANSACTION`
2. `MV_STATE_ROLLUP` — no fast refresh, no query rewrite in PostgreSQL
3. `app/RiskReportDao.java:lapsingSoon` — `date - date` is a NUMBER in Oracle, an INTERVAL in
   PostgreSQL, and the Java reads it with `rs.getInt()`

| Did 8B find it? | Item | Notes |
|---|---|---|
| ☐ | `PKG_FILING_MAINT.log_audit` | |
| ☐ | `MV_STATE_ROLLUP` | |
| ☐ | `RiskReportDao.java:lapsingSoon` | |
| ☐ | anything Capstone 8 missed | |

---

## 3. The validator-independence question

**This is the experiment.** Everything above is instrumentation for it.

In Capstone 8 the validator ran as a subagent with its own context. It had never seen the type
mappings chosen in phase 2 or the load decisions made in phase 3. Its "all clear" was an
independent opinion.

In 8B the validator is the same context that did the work. It is auditing itself.

### The measurement

Run phase 3 **deliberately broken** — omit `null_as` — then run phase 5 and record what
happened. Do this three times, because one trial tells you nothing:

| Run | Did phase 5 report the empty-string defect? | Did it re-query, or cite phase 3? |
|---|---|---|
| 1 | ☐ yes ☐ no | |
| 2 | ☐ yes ☐ no | |
| 3 | ☐ yes ☐ no | |

Check `migration_audit.jsonl` for phase 5 to answer the second column. If the validator emitted
no `pg_query` / `pg_row_count` calls, it did not re-derive anything — it reported from memory,
and a clean result from it means nothing at all.

```bash
python - <<'EOF'
import json
calls = [json.loads(l) for l in open("migration_audit.jsonl", encoding="utf-8")]
reads = [c for c in calls if "pg_query" in c["tool_name"] or "pg_row_count" in c["tool_name"]]
print(f"{len(reads)} target reads during the run")
EOF
```

### Trial 4 — fork the validator

`migration-validation` runs inline like every other skill in this lab. Add one line to its
frontmatter:

```yaml
context: fork
```

It now spawns a subagent: its own context window, only its result returned. That is the property
the inline design gave up, bought back for one line — **without** giving up the single shared
`nullability-preservation` file, which the loader still reads.

Re-run the three trials above with the validator forked:

| Run | Caught the defect? | Re-queried? | Tokens | Wall clock |
|---|---|---|---:|---:|
| 1 | ☐ yes ☐ no | | | |
| 2 | ☐ yes ☐ no | | | |
| 3 | ☐ yes ☐ no | | | |

Then answer honestly:

- Did forking recover Capstone 8's reliability, or only part of it?
- What did the extra turn cost in tokens and wall clock?
- The fork runs under the agent type named in `agent:`, with **that** agent's system prompt —
  not one written for adversarial reconciliation. Did the defect get *caught* but reported
  limply? That gap is the argument for a real subagent, and it belongs here.

### What to conclude

Answer in prose, not a checkbox. Be specific:

> Did the skills-first validator catch the planted defect as reliably as the isolated subagent?
>
> _______________________________________________________________
>
> If it missed it even once: what would you change? Options include a stronger instruction in
> `migration-validation/SKILL.md`, a fresh session for phase 5, or accepting that validation is
> the one phase that genuinely wants isolation.
>
> _______________________________________________________________

---

## 4. The verdict

The point of this lab is that **neither architecture wins outright**, and a professional answer
names the trade rather than picking a side.

Complete these, in your own words:

> Use an **inline skill** when: ______________________________
>
> Use a **forked skill** (`context: fork`) when: _____________
>
> Use a **subagent** when: ___________________________________
>
> For this migration specifically, the shape I would ship is: ____________________
> because ____________________________________________________

A defensible answer here may well be a hybrid — skills for the rulebooks, a subagent for the
validator precisely because it needs not to have seen the work. If that is what your
measurements support, say so. That is the finding, not a failure to pick.
