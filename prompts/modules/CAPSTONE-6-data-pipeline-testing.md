# CAPSTONE-6: Parallel State Testing Agent — Bronze Canonical Load Validation

**Domain**: C — Public Records / UCC Data Engineering
**Difficulty**: ★★★★☆
**Skills Practiced**: M05 (Tools), M06 (Multi-Tool), M12 (ReAct), M13 (Planning), M14 (Multi-Agent), M15B (Build Agent), M16-M17 (Guardrails), M18 (Evaluation)
**Estimated Time**: 4-6 hours across 2-3 sessions
**Prerequisites**: M01-M15B recommended

---

## Business Context

Every quarter, 50 US state Secretary of State (SOS) offices publish bulk UCC filing data. Each state uses its own file format — New York sends XML, California sends pipe-delimited CSV, Texas sends fixed-width text, Florida sends JSON, and so on. There is no federal standard.

The Canonical Loader web tool reads each state's file, applies state-specific transformation rules, and loads into a single **Bronze canonical table** in BigQuery. The Bronze table has one universal schema regardless of which state the data came from.

**The problem you're solving**: After every quarterly load, validate that ALL 50 states loaded correctly into the Bronze canonical table — in parallel, not one at a time. Each state needs its own validation because each has different formats, field mappings, date conventions, and data quirks.

---

## What the Student Builds

A **coordinator agent** that spawns **50 parallel state tester subagents** — one per state. Each subagent:
1. Reads the state's source file (in that state's format)
2. Queries the Bronze table for that state's records
3. Runs 12 validation checks comparing source to Bronze
4. Returns a structured pass/fail report

The coordinator collects all 50 reports, aggregates them, and generates a final dashboard.

---

## The Bronze Canonical Schema

Every state's data normalizes into this ONE table:

```json
{
  "filing_number": "string — unique within state",
  "source_state": "string — 2-letter code",
  "filing_type": "string — UCC1 | UCC3_AMENDMENT | UCC3_CONTINUATION | UCC3_TERMINATION",
  "filing_date": "date — YYYY-MM-DD",
  "lapse_date": "date — YYYY-MM-DD, nullable",
  "status": "string — ACTIVE | TERMINATED | LAPSED",
  "debtor_name": "string — uppercase, trimmed",
  "debtor_address": "string",
  "debtor_org_type": "string — CORPORATION | LLC | PARTNERSHIP | INDIVIDUAL | UNKNOWN",
  "secured_party_name": "string — uppercase, trimmed",
  "secured_party_address": "string",
  "collateral_description": "string",
  "source_file": "string — original filename",
  "load_id": "string — batch identifier",
  "load_timestamp": "timestamp"
}
```

---

## Source Format Registry (5 formats across 50 states)

| Format | States (15 each) | Key Parsing Challenge |
|---|---|---|
| XML | NY, OH, PA, MI, NJ, VA, MA, WA, NC, MD, WI, SC, MN, OR, CT | Nested elements, namespaces |
| Pipe-delimited CSV | CA, IL, GA, CO, AZ, MO, IN, TN, LA, KY, AL, MS, AR, OK, IA | Pipes in collateral text |
| Comma CSV with header | DE, NH, VT, ME, RI, HI, AK, MT, WY, SD, ND, NE, ID, NM, WV | Quoted fields, commas in addresses |
| Fixed-width | TX, FL, KS, UT | Positional parsing, padding |
| JSON | NV plus remaining states | Nested objects, varying keys |

---

## Architecture

```
User: "Run Bronze validation for 2024 Q4 load"
    |
    v
COORDINATOR AGENT
  1. Read load manifest
  2. Spawn 50 state testers IN PARALLEL
  3. Collect 50 results as they stream in
  4. Aggregate into dashboard
    |
    +---> [NY tester] ---> 12 checks ---> result
    +---> [CA tester] ---> 12 checks ---> result
    +---> [TX tester] ---> 12 checks ---> result
    +---> ... (all 50 concurrent) ...
    +---> [WY tester] ---> 12 checks ---> result
```

---

## The 12 Bronze Validation Checks

| # | ID | Check Name | What It Validates |
|---|---|---|---|
| 1 | SRC-01 | Source file parseable | File opens and parses without errors in the state's format |
| 2 | CNT-01 | Record count match | Source record count = Bronze record count for this state |
| 3 | FN-01 | Filing number integrity | Every source filing number exists in Bronze, no extras |
| 4 | DUP-01 | No duplicates in Bronze | No filing_number appears more than once for this state |
| 5 | FT-01 | Filing type normalized | All values are one of 4 canonical types |
| 6 | DT-01 | Date format normalized | All dates in YYYY-MM-DD regardless of source format |
| 7 | DT-02 | Date values valid | No future filing dates, no lapse before filing |
| 8 | ST-01 | Status normalized | All values are ACTIVE, TERMINATED, or LAPSED |
| 9 | NM-01 | Name normalization | Uppercase, trimmed, no double spaces |
| 10 | NL-01 | Required fields not null | 6 required fields are never null |
| 11 | LM-01 | Load metadata present | source_file, load_id, load_timestamp populated |
| 12 | SP-01 | Spot check (3 records) | Random records match field-by-field source to Bronze |

---

## Coordinator Dashboard Output

```
BRONZE CANONICAL LOAD VALIDATION — 2024 Q4

SUMMARY: 47 PASS | 2 FAIL | 1 WARN
Records: 42,350 source -> 42,347 bronze (3 missing)
Duration: 18.4 seconds (50 states in parallel)

FAILURES:
  x NY — DT-02: 2 records have lapse_date before filing_date
  x GA — DT-01: 47 records have DD/MM/YYYY not converted

WARNINGS:
  ! NV — DUP-01: 3 duplicate filing numbers

PER-STATE:
  State | Records | Status | Failed Checks
  NY    |     847 | FAIL   | DT-02
  CA    |   3,421 | PASS   |
  TX    |   1,205 | PASS   |
  ...all 50 states...
  GA    |     987 | FAIL   | DT-01
  NV    |     543 | WARN   | DUP-01
```

---

## File Structure

```
capstone-6-bronze-testing/
├── coordinator.py
├── state_tester.py
├── tools/
│   ├── file_parser.py          # Parses all 5 formats
│   ├── bronze_query.py         # Queries mock Bronze table
│   ├── validation_checks.py    # 12 check implementations
│   └── report_generator.py     # Dashboard + reports
├── mock_data/
│   ├── source_files/           # 15 files (5 formats + error cases)
│   ├── bronze_table.json       # Mock Bronze post-load
│   ├── state_format_registry.json
│   └── load_manifest.json
├── config.py
├── requirements.txt
└── run_tests.py
```

---

## Build Steps

### Step 1: Setup (5 min)
```bash
mkdir -p capstone-6-bronze-testing/{tools,mock_data/source_files}
cd capstone-6-bronze-testing
python -m venv venv && source venv/bin/activate
pip install anthropic pydantic rich
export ANTHROPIC_API_KEY=your-key-here
```
Run: `python -c "import anthropic; print('OK')"`
Expected: `OK`
Checkpoint: Environment ready

### Step 2: config.py — 50-state registry (10 min)
All 50 states with format type and expected record counts.
Run: `python -c "from config import STATES; print(f'{len(STATES)} states')"`
Expected: `50 states`
Checkpoint: All states registered

### Step 3: Mock source files — 15 files across 5 formats (20 min)
Includes error cases: truncated TX, bad encoding FL, empty file, duplicate NV, wrong date format GA.
Run: `ls mock_data/source_files/ | wc -l`
Expected: `15`
Checkpoint: All files present

### Step 4: Mock Bronze table (15 min)
JSON with ~8,500 records from all states, including deliberate issues.
Run: `python -c "import json; d=json.load(open('mock_data/bronze_table.json')); print(len(d))"`
Expected: `~8500`
Checkpoint: Bronze data loaded

### Step 5: file_parser.py — 5-format auto-detecting parser (30 min)
Run: `python -c "from tools.file_parser import parse; r=parse('NY','mock_data/source_files/NY_2024_Q4.xml'); print(len(r))"`
Expected: `847`
Checkpoint: XML parsing works

### Step 6: bronze_query.py — Mock BigQuery queries (20 min)
Run: `python -c "from tools.bronze_query import count('NY'); print(count('NY'))"`
Expected: `847`
Checkpoint: Query returns correct count

### Step 7: validation_checks.py — All 12 checks (45 min)
Run: `python -c "from tools.validation_checks import ALL_CHECKS; print(f'{len(ALL_CHECKS)} checks')"`
Expected: `12 checks`
Checkpoint: All checks importable

### Step 8: state_tester.py — Single state agent (30 min)
Run: `python state_tester.py NY LOAD-2024Q4`
Expected: 10 PASS, 1 FAIL (DT-02), 0 WARN
Run: `python state_tester.py GA LOAD-2024Q4`
Expected: FAIL on DT-01
Checkpoint: Correct pass/fail for known issues

### Step 9: coordinator.py — Parallel 50-state orchestration (45 min)
Run: `python coordinator.py --load-id LOAD-2024Q4-SEED --mode full_seed`
Expected: Dashboard showing 47 PASS, 2 FAIL, 1 WARN
Checkpoint: All 50 states tested in parallel, failures match expected

---

## Three Load Scenarios (the agent must handle all three)

The coordinator accepts a `--mode` flag that determines which checks to run and what baseline to compare against. This mirrors real production: you run different validations for a full seed vs an incremental load vs a schema change.

### SCENARIO A: Full Seed Load (tables start empty, load everything)

**When it runs**: Initial load or full reload of all 50 states into empty Bronze table
**What the coordinator does**:
1. Verifies Bronze table was empty before load (or all records have this load_id)
2. Spawns 50 parallel state testers
3. Each state tester runs all 12 checks
4. No baseline comparison (there's no previous data)

**Mock data used**: `bronze_table_seed.json` — the post-seed-load Bronze table
**Command**: `python coordinator.py --load-id LOAD-2024Q4-SEED --mode full_seed`

**Full seed-specific checks (in addition to the 12 standard checks)**:

| Check | ID | What It Validates |
|---|---|---|
| No pre-existing data | SEED-01 | Bronze had 0 records before load (or 100% of records match this load_id) |
| All 50 states present | SEED-02 | Every state in the registry has at least 1 record in Bronze |
| Total record reconciliation | SEED-03 | Sum of all source file record counts = total Bronze record count |
| Load manifest accuracy | SEED-04 | Manifest claimed X records per state — actual matches |

**Expected dashboard for full seed**:
```
MODE: FULL SEED LOAD
Load ID: LOAD-2024Q4-SEED

SEED CHECKS:
  SEED-01: No pre-existing data     PASS (0 records before load)
  SEED-02: All 50 states present    PASS (50/50 states)
  SEED-03: Total reconciliation     FAIL (source: 42,350, bronze: 42,347, diff: -3)
  SEED-04: Manifest accuracy        WARN (NV manifest says 546, actual 543)

PER-STATE RESULTS (12 checks each):
  47 PASS | 2 FAIL | 1 WARN
  ... [same detail as before] ...
```

### SCENARIO B: Incremental Load (add new quarter's data to existing Bronze)

**When it runs**: Quarterly update — Q1 2025 data loading on top of existing Q4 2024 data
**What the coordinator does**:
1. Reads the BASELINE (Q4 2024 Bronze snapshot) and the CURRENT (post-Q1-2025-load Bronze)
2. Spawns state testers ONLY for states that have new data this quarter
3. Each state tester runs the 12 standard checks PLUS 8 incremental-specific checks
4. Compares current to baseline to detect unintended changes

**Mock data used**:
- `bronze_table_seed.json` — the Q4 2024 baseline
- `bronze_table_incremental.json` — the post-Q1-2025 Bronze table
- `NY_2025_Q1.xml` + `CA_2025_Q1.csv` — new quarter source files
- `load_manifest_2025Q1.json` — incremental load manifest

**Command**: `python coordinator.py --load-id LOAD-2025Q1-INC --mode incremental --baseline LOAD-2024Q4-SEED`

**Incremental-specific checks**:

| Check | ID | What It Validates |
|---|---|---|
| New records added | INC-01 | Bronze count increased by exactly the new source file record count |
| No duplicates from re-load | INC-02 | Filing numbers from Q4 do NOT appear again in Q1 load |
| Existing records untouched | INC-03 | All Q4 records have SAME values as baseline (no unintended overwrites) |
| Load_id differs | INC-04 | Q1 records have load_id LOAD-2025Q1-INC, not LOAD-2024Q4-SEED |
| UCC-3 amendments link | INC-05 | New UCC3_AMENDMENT records reference an existing UCC1 filing_number |
| UCC-3 continuations extend lapse | INC-06 | When UCC3_CONTINUATION loads, the linked UCC1's effective lapse extends by 5 years |
| UCC-3 terminations update status | INC-07 | When UCC3_TERMINATION loads, the linked UCC1's status becomes TERMINATED |
| States without new data unchanged | INC-08 | States not in Q1 manifest have ZERO new records (no phantom inserts) |

**Expected dashboard for incremental**:
```
MODE: INCREMENTAL LOAD
Load ID: LOAD-2025Q1-INC
Baseline: LOAD-2024Q4-SEED

INCREMENTAL CHECKS:
  INC-01: New records added           PASS (NY: +312, CA: +1,205)
  INC-02: No duplicates from re-load  PASS (0 Q4 filing numbers repeated)
  INC-03: Existing records untouched  PASS (42,347 baseline records unchanged)
  INC-04: Load_id differs             PASS (all new records have LOAD-2025Q1-INC)
  INC-05: UCC-3 amendments link       FAIL (3 UCC3 amendments reference non-existent UCC1 filings)
  INC-06: Continuations extend lapse  PASS (15 continuations extended lapse dates correctly)
  INC-07: Terminations update status  PASS (8 terminations marked as TERMINATED)
  INC-08: Unchanged states clean      PASS (48 states with no new data have 0 new records)

PER-STATE RESULTS (states with new data only):
  NY: 12 standard checks — 11 PASS, 1 FAIL (DT-02)
  CA: 12 standard checks — 12 PASS
```

**Deliberate failures baked into mock data**:
- 3 UCC-3 amendments in NY_2025_Q1.xml reference filing numbers that don't exist in the Q4 baseline → INC-05 FAIL
- This tests whether the agent catches orphaned amendments

### SCENARIO C: Change Detection (a state changed their file format)

**When it runs**: Before loading — as a pre-validation step when the source file looks different from previous quarters
**What the coordinator does**:
1. Reads the STATE FORMAT REGISTRY (what format each state SHOULD use)
2. Reads the PREVIOUS quarter's source file for that state (baseline format)
3. Compares the new file's structure to the expected format
4. Flags any structural changes BEFORE the load happens (preventing bad data from entering Bronze)

**Mock data used**:
- `CA_2024_Q4.csv` — California's previous file (pipe-delimited, 15 columns)
- `CA_2025_Q1.csv` — California's new file (pipe-delimited BUT has 16 columns — a new `ORGANIZATION_ID` field added)
- `state_format_registry.json` — expected format per state

**Command**: `python coordinator.py --load-id LOAD-2025Q1-INC --mode change_detection`

**Change detection checks (run BEFORE standard and incremental checks)**:

| Check | ID | What It Validates |
|---|---|---|
| Format type matches registry | CHG-01 | File is still the expected format (XML/CSV/fixed-width/JSON) |
| Column count matches | CHG-02 | Same number of columns/fields as previous quarter |
| Column names match | CHG-03 | Column headers (if present) match previous quarter |
| New columns detected | CHG-04 | Flag any columns in new file that weren't in previous file |
| Removed columns detected | CHG-05 | Flag any columns in previous file that are missing from new file |
| Data type consistency | CHG-06 | Fields that were numeric are still numeric, dates are still dates |
| Delimiter unchanged | CHG-07 | CSV delimiter (pipe vs comma vs tab) matches registry |
| Record volume reasonable | CHG-08 | Record count within 50% of previous quarter (flag if >50% increase or decrease) |
| Date format unchanged | CHG-09 | Date patterns match previous quarter (MM/DD/YYYY vs YYYY-MM-DD) |
| Encoding unchanged | CHG-10 | File encoding matches expected (UTF-8) |

**Expected dashboard for change detection**:
```
MODE: CHANGE DETECTION (pre-load validation)
Comparing: Q1 2025 files vs Q4 2024 baseline

CHANGES DETECTED:
  CA — CHG-04: New column detected: 'ORGANIZATION_ID' (column 16, not in Q4 file)
       CHG-02: Column count changed: Q4 had 15 columns, Q1 has 16 columns
       RECOMMENDATION: Update CA transformation rules before loading

  GA — CHG-09: Date format appears to have changed
       Q4 sample: "10/15/2024" (MM/DD/YYYY)
       Q1 sample: "2025-01-15" (YYYY-MM-DD)
       RECOMMENDATION: Verify date parsing rule handles both formats

ALL OTHER STATES: No changes detected (format, columns, encoding all match Q4)

ACTION REQUIRED: 2 states need transformation rule review before incremental load
```

**Deliberate changes baked into mock data**:
- CA_2025_Q1.csv has 16 columns instead of 15 (new ORGANIZATION_ID field) → CHG-02 + CHG-04
- GA's date format switched from MM/DD/YYYY to YYYY-MM-DD between quarters → CHG-09

---

## Updated Build Steps (continuing from Step 9)

### Step 10: Add full seed scenario to coordinator (20 min)
Add `--mode full_seed` with the 4 seed-specific checks (SEED-01 through SEED-04).
Run: `python coordinator.py --load-id LOAD-2024Q4-SEED --mode full_seed`
Expected: SEED-01 PASS, SEED-02 PASS, SEED-03 FAIL (3 missing), SEED-04 WARN (NV count mismatch)
Checkpoint: Seed-specific checks run and catch the known issues

### Step 11: Create incremental mock data (20 min)
Create `bronze_table_incremental.json` (Q4 baseline + Q1 new records) and Q1 source files (NY_2025_Q1.xml, CA_2025_Q1.csv).
Mock data includes: 3 orphaned UCC-3 amendments, 15 valid continuations, 8 terminations.
Run: `python -c "import json; d=json.load(open('mock_data/bronze_table_incremental.json')); print(len(d))"`
Expected: `~10,000` (8,500 from Q4 + ~1,500 from Q1)
Checkpoint: Incremental Bronze table has more records than seed

### Step 12: Add incremental scenario to coordinator (30 min)
Add `--mode incremental --baseline LOAD-2024Q4-SEED` with 8 incremental-specific checks (INC-01 through INC-08).
Run: `python coordinator.py --load-id LOAD-2025Q1-INC --mode incremental --baseline LOAD-2024Q4-SEED`
Expected: INC-05 FAIL (3 orphaned amendments), all other incremental checks PASS
Checkpoint: Agent catches orphaned UCC-3 references

### Step 13: Add change detection scenario to coordinator (30 min)
Add `--mode change_detection` with 10 change-specific checks (CHG-01 through CHG-10).
Run: `python coordinator.py --load-id LOAD-2025Q1-INC --mode change_detection`
Expected: CA flagged for new column (CHG-02 + CHG-04), GA flagged for date format change (CHG-09)
Checkpoint: Agent catches schema changes before data is loaded

### Step 14: Error scenarios (20 min)
Run: `python state_tester.py TX_BAD LOAD-2024Q4-SEED` — truncated file caught
Run: `python state_tester.py FL_BAD LOAD-2024Q4-SEED` — encoding caught
Run: `python state_tester.py EMPTY LOAD-2024Q4-SEED` — empty handled
Checkpoint: All errors handled, no crashes

### Step 15: Full suite — all three modes in sequence (20 min)
```bash
# Step 1: Change detection (pre-load check)
python coordinator.py --mode change_detection --output reports/

# Step 2: Full seed validation
python coordinator.py --load-id LOAD-2024Q4-SEED --mode full_seed --output reports/

# Step 3: Incremental validation
python coordinator.py --load-id LOAD-2025Q1-INC --mode incremental --baseline LOAD-2024Q4-SEED --output reports/
```
Expected: 3 separate reports generated, each with mode-specific results
🎉 Congratulations: Complete data pipeline test automation system with full seed, incremental, and change detection coverage

---

## Error Scenarios

| File | Issue | Expected Agent Behavior |
|---|---|---|
| TX_BAD_truncated.dat | Last record cut off | SRC-01 FAIL: "File truncated, last record incomplete" |
| FL_BAD_encoding.json | UTF-16 instead of UTF-8 | SRC-01 FAIL: "Expected UTF-8, detected UTF-16LE" |
| EMPTY_STATE.csv | No data records | All PASS: 0 source = 0 bronze is valid |
| NV_2024_Q4.json | 3 duplicate filing numbers | DUP-01 WARN: "3 duplicates found" |
| GA_2024_Q4.csv | DD/MM/YYYY dates | DT-01 FAIL: "47 records not converted to YYYY-MM-DD" |
| NY records | 2 lapse < filing | DT-02 FAIL: "2 records with lapse before filing date" |
| NY_2025_Q1.xml | 3 orphaned UCC-3 amendments | INC-05 FAIL: "3 amendments reference non-existent filings" |
| CA_2025_Q1.csv | New column added | CHG-02 + CHG-04: "Column count 15→16, new: ORGANIZATION_ID" |
| GA Q1 dates | Format switched to YYYY-MM-DD | CHG-09: "Date format changed from MM/DD/YYYY to YYYY-MM-DD" |

---

## Complete Check Summary (12 standard + 4 seed + 8 incremental + 10 change detection = 34 checks)

| Mode | Checks | IDs |
|---|---|---|
| All modes | 12 standard per-state checks | SRC-01, CNT-01, FN-01, DUP-01, FT-01, DT-01, DT-02, ST-01, NM-01, NL-01, LM-01, SP-01 |
| Full seed only | 4 seed-specific checks | SEED-01, SEED-02, SEED-03, SEED-04 |
| Incremental only | 8 incremental-specific checks | INC-01 through INC-08 |
| Change detection only | 10 change-specific checks | CHG-01 through CHG-10 |

---

## Going Further (Optional)
1. Build an MCP server for conversational test execution ("Hey Claude, how did Georgia's load go?")
2. Add a "fix recommendation" agent that suggests transformation rule updates when changes are detected
3. Add trend analysis — compare this quarter's results to last 4 quarters, flag anomalies

---

## Running in Production Mode

The student's capstone works locally with mock data. This section teaches how to run the SAME agent in a real production environment — connected to real BigQuery tables, triggered automatically after every data load, with alerting and audit trails.

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION PIPELINE                           │
│                                                                  │
│  [Canonical Loader]                                              │
│       │                                                          │
│       │ Load completes → publishes event                         │
│       ▼                                                          │
│  [Cloud Pub/Sub Topic: "load-complete"]                          │
│       │                                                          │
│       │ Triggers                                                 │
│       ▼                                                          │
│  [Cloud Run Service: bronze-test-agent]                          │
│       │                                                          │
│       ├──→ Reads source files from GCS bucket                    │
│       ├──→ Queries Bronze table in BigQuery                      │
│       ├──→ Spawns 50 parallel state testers                      │
│       ├──→ Writes results to BigQuery test_results table         │
│       ├──→ Writes report to GCS reports/ bucket                  │
│       │                                                          │
│       ├──→ ALL PASS? → Slack: "✅ Q1 2025 load validated"        │
│       └──→ ANY FAIL? → Slack: "🚨 2 states FAILED" + PagerDuty  │
│                                                                  │
│  [Grafana Dashboard]                                             │
│       └──→ Reads from BigQuery test_results table                │
│       └──→ Shows: pass rate trends, per-state history,           │
│            check failure frequency, load validation duration      │
└─────────────────────────────────────────────────────────────────┘
```

### Step 16: Replace mock tools with real BigQuery + GCS connections (45 min)

**What changes from local to production**:

| Local (mock) | Production (real) | What to change |
|---|---|---|
| `mock_data/source_files/` | GCS bucket `gs://ucc-pipeline-source/{state}/{quarter}/` | `file_parser.py`: read from GCS instead of local disk |
| `mock_data/bronze_table.json` | BigQuery table `ucc_pipeline.bronze_filings` | `bronze_query.py`: use `google-cloud-bigquery` SDK instead of JSON file |
| Print dashboard to terminal | Write results to BigQuery `ucc_pipeline.test_results` table | `report_generator.py`: insert rows via BigQuery client |
| Reports saved to `reports/` folder | Reports saved to GCS `gs://ucc-pipeline-reports/{date}/` | `report_generator.py`: upload to GCS |

**The key**: the coordinator and state_tester agents DON'T CHANGE. Only the tool implementations change. This is why the tool abstraction matters — the agent calls `query_bronze("NY")` whether that queries a JSON file or BigQuery.

```python
# bronze_query.py — production version
# pip install google-cloud-bigquery

from google.cloud import bigquery

client = bigquery.Client(project="your-gcp-project")
DATASET = "ucc_pipeline"

def get_state_records(state_code: str, load_id: str) -> list[dict]:
    """Query Bronze table for a specific state and load."""
    query = f"""
        SELECT *
        FROM `{DATASET}.bronze_filings`
        WHERE source_state = @state
        AND load_id = @load_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("state", "STRING", state_code),
            bigquery.ScalarQueryParameter("load_id", "STRING", load_id),
        ]
    )
    return [dict(row) for row in client.query(query, job_config=job_config)]

def get_record_count(state_code: str, load_id: str) -> int:
    """Count Bronze records for a state."""
    query = f"""
        SELECT COUNT(*) as cnt
        FROM `{DATASET}.bronze_filings`
        WHERE source_state = @state
        AND load_id = @load_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("state", "STRING", state_code),
            bigquery.ScalarQueryParameter("load_id", "STRING", load_id),
        ]
    )
    rows = list(client.query(query, job_config=job_config))
    return rows[0]["cnt"] if rows else 0
```

Run: Verify connection with `python -c "from tools.bronze_query import get_record_count; print(get_record_count('NY', 'LOAD-2024Q4-SEED'))"`
Expected: Actual record count from BigQuery
Checkpoint: BigQuery connection works, query returns data

### Step 17: Wrap coordinator as a Cloud Run service (30 min)

```python
# server.py — FastAPI wrapper for the coordinator
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Bronze Test Agent")

class TestRequest(BaseModel):
    load_id: str
    mode: str  # full_seed | incremental | change_detection
    baseline_load_id: str | None = None

class TestResult(BaseModel):
    status: str  # PASS | FAIL | WARN
    summary: dict
    report_url: str

@app.post("/validate", response_model=TestResult)
async def run_validation(request: TestRequest, background_tasks: BackgroundTasks):
    """Run Bronze validation — called by Pub/Sub or manually."""
    from coordinator import run_coordinator

    result = await run_coordinator(
        load_id=request.load_id,
        mode=request.mode,
        baseline=request.baseline_load_id,
    )

    # Write results to BigQuery + GCS in background (don't block response)
    background_tasks.add_task(save_results, result)
    background_tasks.add_task(send_notifications, result)

    return TestResult(
        status=result["overall_status"],
        summary=result["summary"],
        report_url=result["report_gcs_url"],
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
```

Dockerfile, deployment command, and IAM setup follow the same pattern as M22B.

Run: `docker build -t bronze-test-agent . && docker run -p 8000:8000 -e GOOGLE_APPLICATION_CREDENTIALS=... bronze-test-agent`
Test: `curl -X POST http://localhost:8000/validate -H "Content-Type: application/json" -d '{"load_id": "LOAD-2024Q4-SEED", "mode": "full_seed"}'`
Checkpoint: Returns JSON result with status, summary, and report URL

### Step 18: Set up Pub/Sub trigger (20 min)

The Canonical Loader publishes an event to Pub/Sub when a load completes. The test agent subscribes and auto-runs.

```python
# pubsub_trigger.py — Cloud Run Pub/Sub push endpoint
from fastapi import FastAPI, Request
import base64, json

@app.post("/pubsub")
async def handle_pubsub(request: Request):
    """Called by Pub/Sub when Canonical Loader completes a load."""
    envelope = await request.json()
    message_data = base64.b64decode(envelope["message"]["data"]).decode()
    event = json.loads(message_data)

    # Event from Canonical Loader:
    # {"load_id": "LOAD-2025Q1-INC", "mode": "incremental",
    #  "baseline": "LOAD-2024Q4-SEED", "states_loaded": ["NY", "CA"]}

    # Auto-run validation
    from coordinator import run_coordinator
    result = await run_coordinator(
        load_id=event["load_id"],
        mode=event["mode"],
        baseline=event.get("baseline"),
    )

    await save_results(result)
    await send_notifications(result)
    return {"status": "processed"}
```

GCP setup:
```bash
# Create Pub/Sub topic
gcloud pubsub topics create load-complete

# Deploy Cloud Run with Pub/Sub trigger
gcloud run deploy bronze-test-agent \
  --image us-docker.pkg.dev/YOUR_PROJECT/agents/bronze-test-agent:v1 \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 3

# Create Pub/Sub subscription that pushes to Cloud Run
gcloud pubsub subscriptions create load-complete-sub \
  --topic=load-complete \
  --push-endpoint=https://bronze-test-agent-xxxxx.run.app/pubsub
```

Checkpoint: Canonical Loader publishes to Pub/Sub → test agent auto-runs → results in BigQuery + Slack

### Step 19: Add Slack alerting (15 min)

```python
# notifications.py
import httpx

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

async def send_notifications(result: dict):
    """Send Slack notification based on test results."""
    status = result["overall_status"]
    summary = result["summary"]
    load_id = result["load_id"]

    if status == "PASS":
        color = "#22c55e"
        emoji = "✅"
        text = f"{emoji} Bronze validation PASSED for {load_id}"
        detail = f"{summary['pass_count']}/{summary['total_states']} states passed all checks"

    elif status == "FAIL":
        color = "#ef4444"
        emoji = "🚨"
        failed_states = ", ".join(summary["failed_states"])
        text = f"{emoji} Bronze validation FAILED for {load_id}"
        detail = f"Failed states: {failed_states}\nSee report: {result['report_gcs_url']}"

    else:  # WARN
        color = "#f59e0b"
        emoji = "⚠️"
        text = f"{emoji} Bronze validation PASSED WITH WARNINGS for {load_id}"
        detail = f"Warnings in: {', '.join(summary['warn_states'])}"

    payload = {
        "attachments": [{
            "color": color,
            "title": text,
            "text": detail,
            "footer": f"Duration: {summary['duration_seconds']:.1f}s | Mode: {result['mode']}",
        }]
    }

    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json=payload)
```

Checkpoint: FAIL result sends red Slack alert with failed states and report link

### Step 20: Set up Grafana monitoring dashboard (20 min)

The test results table in BigQuery powers a Grafana dashboard:

```sql
-- BigQuery table: ucc_pipeline.test_results
CREATE TABLE ucc_pipeline.test_results (
    load_id STRING,
    mode STRING,
    run_timestamp TIMESTAMP,
    state STRING,
    check_id STRING,
    check_name STRING,
    status STRING,  -- PASS | FAIL | WARN
    details STRING,
    duration_seconds FLOAT64
);
```

Grafana panels:
1. **Pass rate over time** — line chart showing % of states passing per quarter
2. **Per-state health map** — US map with red/green/yellow per state (last run)
3. **Most failing checks** — bar chart showing which checks fail most often
4. **Average validation duration** — trend line per quarter
5. **Failure detail table** — filterable table of all FAIL results with state, check, details

Query for pass rate panel:
```sql
SELECT
    load_id,
    COUNTIF(status = 'PASS') / COUNT(*) * 100 as pass_rate
FROM `ucc_pipeline.test_results`
WHERE check_id = 'CNT-01'  -- or any single check as proxy
GROUP BY load_id
ORDER BY load_id
```

### Step 21: Schedule regular validation runs (10 min)

For ongoing monitoring beyond load-triggered runs:

```bash
# Cloud Scheduler — run full validation every Sunday midnight
gcloud scheduler jobs create http bronze-weekly-validation \
  --schedule="0 0 * * SUN" \
  --uri="https://bronze-test-agent-xxxxx.run.app/validate" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"load_id": "LATEST", "mode": "full_seed"}' \
  --time-zone="America/New_York"
```

This catches data drift — records that were valid at load time but have since become invalid (lapsed filings not updated, status changes not reflected).

### Production Mode Summary — Three Deployment Tiers

The capstone supports THREE deployment tiers. Students choose based on their environment. The coordinator and state_tester agents are IDENTICAL across all three — only the tool implementations change.

#### TIER 1: Local Production (no cloud account needed) ← START HERE

For students without GCP/AWS access. Uses Docker + DuckDB + local filesystem. This is a REAL production setup — containerized, with a database, API server, file watcher, and dashboard — just running on your laptop instead of the cloud.

**What you need**: Docker Desktop installed. Nothing else.

**Step 16L: Create DuckDB Bronze table (15 min)**

DuckDB is a local analytical database (like SQLite but for analytics). It replaces BigQuery with zero setup.

```python
# tools/bronze_query_local.py
# pip install duckdb
import duckdb
import json

DB_PATH = "data/bronze.duckdb"

def init_db():
    """Create Bronze table and load mock data into DuckDB."""
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS bronze_filings (
            filing_number VARCHAR,
            source_state VARCHAR(2),
            filing_type VARCHAR,
            filing_date DATE,
            lapse_date DATE,
            status VARCHAR,
            debtor_name VARCHAR,
            debtor_address VARCHAR,
            debtor_org_type VARCHAR,
            secured_party_name VARCHAR,
            secured_party_address VARCHAR,
            collateral_description VARCHAR,
            source_file VARCHAR,
            load_id VARCHAR,
            load_timestamp TIMESTAMP
        )
    """)
    # Load mock data
    with open("mock_data/bronze_table.json") as f:
        records = json.load(f)
    for r in records:
        con.execute("""
            INSERT INTO bronze_filings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, list(r.values()))
    con.close()
    print(f"Loaded {len(records)} records into DuckDB")

def get_state_records(state_code: str, load_id: str) -> list[dict]:
    """Same interface as BigQuery version — drop-in replacement."""
    con = duckdb.connect(DB_PATH, read_only=True)
    result = con.execute(
        "SELECT * FROM bronze_filings WHERE source_state = ? AND load_id = ?",
        [state_code, load_id]
    ).fetchdf().to_dict('records')
    con.close()
    return result

def get_record_count(state_code: str, load_id: str) -> int:
    con = duckdb.connect(DB_PATH, read_only=True)
    count = con.execute(
        "SELECT COUNT(*) FROM bronze_filings WHERE source_state = ? AND load_id = ?",
        [state_code, load_id]
    ).fetchone()[0]
    con.close()
    return count
```

Run: `python -c "from tools.bronze_query_local import init_db; init_db()"`
Expected: `Loaded ~8500 records into DuckDB`

Run: `python -c "from tools.bronze_query_local import get_record_count; print(get_record_count('NY', 'LOAD-2024Q4-SEED'))"`
Expected: `847`
Checkpoint: DuckDB works as BigQuery replacement

**Step 17L: Create test results table in DuckDB (10 min)**

```python
# tools/results_db.py
import duckdb
from datetime import datetime

def save_results(results: list[dict]):
    """Save test results to DuckDB — same data that would go to BigQuery in production."""
    con = duckdb.connect("data/bronze.duckdb")
    con.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            load_id VARCHAR,
            mode VARCHAR,
            run_timestamp TIMESTAMP,
            state VARCHAR(2),
            check_id VARCHAR,
            check_name VARCHAR,
            status VARCHAR,
            details VARCHAR,
            duration_seconds FLOAT
        )
    """)
    for r in results:
        con.execute(
            "INSERT INTO test_results VALUES (?,?,?,?,?,?,?,?,?)",
            [r["load_id"], r["mode"], datetime.now(), r["state"],
             r["check_id"], r["check_name"], r["status"], r["details"],
             r["duration_seconds"]]
        )
    con.close()

def query_results(load_id: str = None) -> list[dict]:
    """Query test results — same interface as BigQuery would use."""
    con = duckdb.connect("data/bronze.duckdb", read_only=True)
    if load_id:
        df = con.execute("SELECT * FROM test_results WHERE load_id = ?", [load_id]).fetchdf()
    else:
        df = con.execute("SELECT * FROM test_results ORDER BY run_timestamp DESC LIMIT 1000").fetchdf()
    con.close()
    return df.to_dict('records')
```

Checkpoint: Results persist across runs — you can query historical test results

**Step 18L: Docker Compose local production stack (20 min)**

```yaml
# docker-compose.yml
version: '3.8'
services:
  # The test agent API
  test-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEPLOYMENT_TIER=local
      - DB_PATH=/data/bronze.duckdb
    volumes:
      - ./data:/data                    # DuckDB persists here
      - ./mock_data:/app/mock_data      # Source files
      - ./reports:/app/reports          # Generated reports

  # File watcher — auto-triggers validation when new source files appear
  file-watcher:
    build: .
    command: python file_watcher.py
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AGENT_URL=http://test-agent:8000
    volumes:
      - ./mock_data/source_files:/watch  # Watches this folder for new files

  # Local dashboard (optional — uses built-in HTML dashboard)
  dashboard:
    build: .
    command: python dashboard_server.py
    ports:
      - "8080:8080"
    environment:
      - DB_PATH=/data/bronze.duckdb
    volumes:
      - ./data:/data
```

```bash
# Start everything
docker compose up -d

# Test the agent API
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"load_id": "LOAD-2024Q4-SEED", "mode": "full_seed"}'

# View the dashboard
open http://localhost:8080
```

Checkpoint: Three containers running — agent API, file watcher, dashboard

**Step 19L: File watcher — auto-trigger on new source files (15 min)**

```python
# file_watcher.py
# Watches a folder for new files and auto-triggers validation
import os, time, httpx

WATCH_DIR = os.environ.get("WATCH_DIR", "/watch")
AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8000")
SEEN_FILES = set()

def detect_load_from_files(new_files: list[str]) -> dict:
    """Infer load_id and mode from the new file names."""
    # E.g., NY_2025_Q1.xml → load_id=LOAD-2025Q1, mode=incremental
    quarters = set()
    for f in new_files:
        parts = f.replace(".xml", "").replace(".csv", "").replace(".json", "").replace(".dat", "").split("_")
        if len(parts) >= 3:
            quarters.add(f"{parts[1]}_{parts[2]}")
    quarter = quarters.pop() if quarters else "UNKNOWN"
    load_id = f"LOAD-{quarter.replace('_', '')}"

    # If this is the first load (no previous results), it's a seed
    # Otherwise it's incremental
    mode = "full_seed"  # simplified — production would check test_results table
    return {"load_id": load_id, "mode": mode}

print(f"Watching {WATCH_DIR} for new source files...")
while True:
    current_files = set(os.listdir(WATCH_DIR))
    new_files = current_files - SEEN_FILES
    if new_files:
        print(f"New files detected: {new_files}")
        load_info = detect_load_from_files(list(new_files))
        # Auto-trigger validation
        response = httpx.post(f"{AGENT_URL}/validate", json=load_info)
        print(f"Validation triggered: {response.json()}")
        SEEN_FILES.update(new_files)
    time.sleep(10)  # Check every 10 seconds
```

Test: drop a new file into `mock_data/source_files/` → file watcher detects it → triggers validation automatically
Checkpoint: Auto-trigger works without manual intervention

**Step 20L: Local HTML dashboard (20 min)**

```python
# dashboard_server.py
# Simple HTML dashboard served locally — no Grafana needed
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import duckdb

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    con = duckdb.connect(os.environ.get("DB_PATH", "data/bronze.duckdb"), read_only=True)

    # Latest run summary
    summary = con.execute("""
        SELECT
            load_id,
            COUNT(*) as total_checks,
            SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) as pass_count,
            SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) as fail_count,
            SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) as warn_count,
            MAX(run_timestamp) as last_run
        FROM test_results
        GROUP BY load_id
        ORDER BY last_run DESC
        LIMIT 5
    """).fetchdf().to_dict('records')

    # Failed checks detail
    failures = con.execute("""
        SELECT state, check_id, check_name, details, run_timestamp
        FROM test_results
        WHERE status = 'FAIL'
        ORDER BY run_timestamp DESC
        LIMIT 20
    """).fetchdf().to_dict('records')

    con.close()

    # Generate HTML dashboard (self-contained, styled)
    # Uses the same dark theme as the course modules
    html = f"""
    <!DOCTYPE html>
    <html><head><title>Bronze Validation Dashboard</title>
    <style>
      body {{ background: #0A1628; color: #E8ECF1; font-family: sans-serif; padding: 2rem; }}
      h1 {{ color: #D4A843; }}
      table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
      th {{ background: rgba(255,255,255,0.06); padding: 8px 12px; text-align: left; }}
      td {{ padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
      .pass {{ color: #10B981; }} .fail {{ color: #F43F5E; }} .warn {{ color: #F59E0B; }}
    </style></head><body>
    <h1>Bronze Canonical Load Validation Dashboard</h1>
    <h2>Recent Runs</h2>
    <table><tr><th>Load ID</th><th>Total</th><th>Pass</th><th>Fail</th><th>Warn</th><th>Last Run</th></tr>
    {"".join(f"<tr><td>{r['load_id']}</td><td>{r['total_checks']}</td><td class='pass'>{r['pass_count']}</td><td class='fail'>{r['fail_count']}</td><td class='warn'>{r['warn_count']}</td><td>{r['last_run']}</td></tr>" for r in summary)}
    </table>
    <h2>Recent Failures</h2>
    <table><tr><th>State</th><th>Check</th><th>Details</th><th>When</th></tr>
    {"".join(f"<tr><td>{r['state']}</td><td>{r['check_id']}: {r['check_name']}</td><td>{r['details']}</td><td>{r['run_timestamp']}</td></tr>" for r in failures)}
    </table>
    </body></html>
    """
    return html
```

Run: `open http://localhost:8080`
Expected: Dark-themed dashboard showing recent runs, pass/fail counts, and failure details
Checkpoint: Dashboard displays data from DuckDB — no cloud services needed

---

#### TIER 2: Cloud Production — GCP (needs GCP account)
Steps 16-21 as described above (BigQuery + Cloud Run + Pub/Sub + Grafana + Cloud Scheduler)

#### TIER 3: Cloud Production — AWS (needs AWS account)
Same pattern but with:
- DynamoDB or Athena instead of BigQuery
- Lambda instead of Cloud Run
- SNS instead of Pub/Sub
- EventBridge instead of Cloud Scheduler
- S3 instead of GCS

(Architecture pattern is identical — only the cloud service names change)

---

### Three-Tier Comparison

| Component | Tier 1: Local | Tier 2: GCP | Tier 3: AWS |
|---|---|---|---|
| Bronze table | DuckDB (local file) | BigQuery | Athena/DynamoDB |
| Source files | Local folder | GCS bucket | S3 bucket |
| Test results DB | DuckDB | BigQuery table | DynamoDB |
| Reports | Local `reports/` | GCS bucket | S3 bucket |
| API hosting | Docker Compose | Cloud Run | Lambda + API Gateway |
| Auto-trigger | File watcher (watchdog) | Pub/Sub | S3 event → SNS → Lambda |
| Dashboard | Local HTML + DuckDB | Grafana + BigQuery | QuickSight + Athena |
| Scheduling | cron on host machine | Cloud Scheduler | EventBridge |
| Alerting | Terminal + desktop notification | Slack + PagerDuty | Slack + SNS |
| Cost | $0 (just Anthropic API) | ~$0.05/run | ~$0.05/run |
| Setup time | 15 min | 45 min | 45 min |
| Cloud account needed | No | Yes (GCP) | Yes (AWS) |

**The teaching progression**: Every student builds Tier 1 first. Students with cloud access THEN upgrade to Tier 2 or 3. The agent code is identical — only the tool implementations swap.

**The critical insight**: The coordinator agent and state_tester agents are IDENTICAL across ALL THREE TIERS. Only the TOOLS change (DuckDB → BigQuery → Athena, local folder → GCS → S3, file watcher → Pub/Sub → SNS). This is why clean tool abstraction matters — it makes deployment a tool-swap, not a rewrite.

---

## Architecture Diagrams & Animations

This capstone MUST include the following visual elements. These are not decorative — they explain the system the student is building and help them understand the flow before writing code.

### ANIMATION 1: The 50-State Problem (show BEFORE building anything)
**Purpose**: Show WHY this capstone exists — the scale of the problem
**Type**: Animated US map
**Behavior**:
- Step 1: US map appears with all 50 states outlined
- Step 2: States light up in 5 different colors representing their file format (XML=blue, pipe-CSV=green, comma-CSV=orange, fixed-width=red, JSON=purple)
- Step 3: Legend appears showing format distribution
- Step 4: Arrows flow from each state toward a central "Bronze Canonical Table" box
- Step 5: The central box shows the canonical schema fields appearing one by one
- Step 6: Label appears: "50 formats → 1 schema. Your agent validates every transformation."
**Controls**: Play/pause/restart. Step-through to pause at each stage.

### ANIMATION 2: Parallel Agent Swarm
**Purpose**: Show the coordinator spawning 50 subagents concurrently
**Type**: Animated agent orchestration diagram
**Behavior**:
- Step 1: Coordinator box at the top with "Run Bronze validation" message arriving
- Step 2: Coordinator reads the load manifest (small file icon animation)
- Step 3: 50 subagent boxes burst outward from the coordinator simultaneously (not one-by-one — this must visually feel PARALLEL)
- Step 4: Each subagent box shows its state code (NY, CA, TX...) and starts a spinning loader
- Step 5: Results stream back — some turn green (PASS), some turn red (FAIL), one turns yellow (WARN). They DON'T all finish at the same time — some finish faster (small states), some slower (large states like CA)
- Step 6: All results flow back into the coordinator, which produces the dashboard
**Controls**: Play/pause/restart. Speed slider (1x, 2x, 5x).

### ANIMATION 3: Single State Validation Flow
**Purpose**: Show what happens INSIDE one state tester subagent
**Type**: Pipeline flow with 12 check gates
**Behavior**:
- Step 1: State tester receives "Validate NY" command
- Step 2: Left side: source file (NY_2024_Q4.xml) opens, records stream out as small blocks
- Step 3: Right side: Bronze table query runs, matching records appear as blocks
- Step 4: The 12 checks appear as gates between source and Bronze:
  - Each gate has the check name (SRC-01, CNT-01, FN-01...)
  - Records flow through each gate
  - Gate turns green (pass) or red (fail) based on the check result
  - For the failing check (DT-02 for NY), the gate turns red and 2 blocks get flagged
- Step 5: Result summary appears at the bottom: "10 PASS, 1 FAIL, 0 WARN"
**Controls**: Play/pause/restart/step-through-each-check.

### ANIMATION 4: Format Parsing Comparison
**Purpose**: Show how the same UCC filing looks in all 5 formats
**Type**: Side-by-side format viewer
**Behavior**:
- Center: One canonical Bronze record (the "target")
- 5 panels around it, each showing the SAME filing in a different format:
  - XML panel: highlighted nested elements mapping to canonical fields
  - Pipe-CSV panel: highlighted pipe-separated values with field arrows
  - Comma-CSV panel: highlighted comma-separated with header row
  - Fixed-width panel: highlighted character positions with ruler
  - JSON panel: highlighted nested objects mapping to canonical fields
- Animated lines connect each format's fields to the canonical record's fields
- Color coding: same field = same color across all formats
- Learner can click any format to highlight just that mapping
**Controls**: Click each format tab. Play full animation showing all 5 sequentially.

### ANIMATION 5: The 12 Checks Explained
**Purpose**: Visual reference card for all 12 validation checks
**Type**: Interactive check grid
**Behavior**:
- 4×3 grid of check cards, each showing:
  - Check ID and name
  - Icon (green checkmark for typical pass, red X for the known failure scenarios)
  - One-sentence description
- Click any card to expand:
  - What it checks (2-3 sentences)
  - Example PASS case (with data)
  - Example FAIL case (with data showing what went wrong)
  - Which states trigger failures in the mock data
- The grid auto-highlights the 3 checks that have known failures in the mock data (DT-01, DT-02, DUP-01)
**Controls**: Click to expand/collapse each card. "Show failures only" filter button.

### ANIMATION 6: Dashboard Assembly
**Purpose**: Show how 50 individual results aggregate into the final dashboard
**Type**: Animated data aggregation
**Behavior**:
- Step 1: 50 small result cards fly in (each with state code + pass/fail)
- Step 2: Cards sort into three columns: PASS (green), FAIL (red), WARN (yellow)
- Step 3: Count numbers animate up: "47 PASS | 2 FAIL | 1 WARN"
- Step 4: The per-check summary row builds — each check shows its pass/fail count across all 50 states
- Step 5: The final dashboard "locks in" and a "Report saved" confirmation appears
**Controls**: Play/pause/restart.

### ANIMATION 7: Error Scenario Gallery
**Purpose**: Show each error case and how the agent handles it
**Type**: Tabbed error scenario viewer
**Behavior**:
- 6 tabs, one per error scenario (truncated, encoding, empty, duplicates, dates, invalid dates)
- Each tab shows:
  - The problematic file (highlighted problem area)
  - Arrow pointing to the check that catches it
  - The agent's response (structured error message)
  - The dashboard entry showing the FAIL/WARN
- Tabs auto-cycle every 5 seconds or click to jump
**Controls**: Tab click. Auto-cycle on/off. Pause.

### STATIC DIAGRAM 1: Project File Structure
**Purpose**: Visual directory tree showing every file the student will create
**Type**: Interactive file tree (expand/collapse folders)
- Click any file to see a 1-sentence description of what it contains
- Color-coded: tools (green), mock data (blue), agents (orange), config (gray)

### STATIC DIAGRAM 2: Data Flow — Source to Bronze
**Purpose**: Show the transformation pipeline the Canonical Loader performs (what the agent TESTS, not builds)
**Type**: Left-to-right flow diagram
```
[50 Source Files] → [Format Detection] → [State-Specific Parser] → [Field Mapping] → [Normalization] → [Bronze Table]
                                                                                                              ↑
                                                                                    [Your Agent Tests THIS] ──┘
```
- Each stage labeled with which check validates it
- "Your agent doesn't BUILD this pipeline — it TESTS it"
