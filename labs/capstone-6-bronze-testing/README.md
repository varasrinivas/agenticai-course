# Capstone 6: Data Pipeline Testing -- Parallel State Validation Agent

## What You'll Build

A **coordinator agent** that spawns **parallel state tester subagents**, each validating one state's UCC filing data load into a Bronze canonical table. The system processes **16 states**, **5 file formats**, and runs **12 validation checks** per state.

Architecture:

```
Coordinator Agent
  |
  +-- ThreadPoolExecutor (max_workers=5)
       |
       +-- StateTester("NY")  --> parse XML   --> 12 checks --> result
       +-- StateTester("CA")  --> parse pipe  --> 12 checks --> result
       +-- StateTester("TX")  --> parse fixed --> 12 checks --> result
       +-- StateTester("FL")  --> parse JSON  --> 12 checks --> result
       +-- ...  (16 states total, including 2 intentional error files)
       |
  +-- Dashboard
       +-- Console table
       +-- HTML report (color-coded)
       +-- JSON report (machine-readable)
```

## Difficulty: 4/5 (4-6 hours)

## Prerequisites

- Modules M05-M06 (tool use), M12 (ReAct), M13-M14 (multi-agent), M15B (build lab), M16-M18 (guardrails/observability)
- Python 3.10+
- Docker Desktop (for Step 9)

## Setup

```bash
# Navigate to this capstone
cd labs/capstone-6-bronze-testing

# Work in the starter directory
cd starter

# Install dependencies
pip install -r requirements.txt

# Verify mock data is present
ls mock_data/source_files/
# Should show 16 files: NY_2024_Q4.xml, CA_2024_Q4.csv, ... TX_BAD_truncated.dat, FL_BAD_encoding.json
```

## The 12 Bronze Validation Checks

Each state tester runs all 12 checks against the Bronze table records for its state:

| Check ID | Check Name                    | What It Validates                                          |
|----------|-------------------------------|-----------------------------------------------------------|
| SRC-01   | Source File Parseable         | Can the source file be read and parsed without errors?     |
| CNT-01   | Record Count Match            | Do source and Bronze record counts match?                  |
| FN-01    | Filing Number Integrity       | Do filing numbers match pattern `XX-YYYY-NNNN`?           |
| DUP-01   | No Duplicate Filing Numbers   | Are there any duplicate filing numbers in Bronze?          |
| FT-01    | Filing Type Normalized        | Are filing types from the valid set (UCC1, UCC3_*, UCC5)? |
| DT-01    | Date Format Valid             | Are all dates in YYYY-MM-DD format?                        |
| DT-02    | Date Values Valid             | Are lapse dates after filing dates? No future dates?       |
| ST-01    | Status Normalized             | Are statuses from the valid set (ACTIVE, TERMINATED, LAPSED)? |
| NM-01    | Name Normalization            | Are names uppercase, trimmed, no double spaces?            |
| NL-01    | Required Fields Not Null      | Are all required fields populated?                         |
| LM-01    | Load Metadata Present         | Do records have load_timestamp, batch_id, source_file?     |
| SP-01    | Spot Check Sample             | Do random Bronze records match their source file records?   |

## The 5 Source File Formats

| Format       | Parser Module         | States Using It         | Example File       |
|--------------|-----------------------|-------------------------|--------------------|
| XML          | `xml_parser.py`       | NY, IL, WA              | NY_2024_Q4.xml     |
| Pipe CSV     | `pipe_csv_parser.py`  | CA, OH, GA, CO          | CA_2024_Q4.csv     |
| Comma CSV    | `comma_csv_parser.py` | DE, PA, MA              | DE_2024_Q4.csv     |
| Fixed-Width  | `fixed_width_parser.py` | TX                    | TX_2024_Q4.dat     |
| JSON         | `json_parser.py`      | FL, NV                  | FL_2024_Q4.json    |

## Known Issues in Test Data

The mock data includes intentional issues for you to detect:

- **GA**: Dates are in DD/MM/YYYY format instead of YYYY-MM-DD (DT-01 and DT-02 should flag this)
- **NV**: Contains 3 duplicate filing numbers (DUP-01 should warn)
- **TX_BAD**: Truncated fixed-width file (SRC-01 should fail)
- **FL_BAD**: UTF-16LE BOM encoding instead of UTF-8 (SRC-01 should fail)

---

## Step-by-Step Lab Instructions

### Step 1: Understand the Architecture

Read through the three main files to understand the data flow:

1. **`coordinator.py`** -- Loads the manifest and Bronze table, spawns parallel state testers, collects results
2. **`state_tester.py`** -- Parses one state's source file, runs all 12 checks, returns structured results
3. **`dashboard.py`** -- Aggregates results into console, HTML, and JSON reports

Also review:
- `mock_data/load_manifest.json` -- Describes all 16 states, their source files, and formats
- `mock_data/bronze_table.json` -- The canonical Bronze table with 195 sample records
- `mock_data/state_format_registry.json` -- Maps each state code to its file format

### Step 2: Implement the Parsers

Open each file in `parsers/` and complete the TODOs. Each parser must:
1. Read the source file from disk
2. Parse records into a list of dicts with normalized field names
3. Return `(records, metadata)` tuple
4. Raise an exception if the file cannot be parsed

Start with the simplest format and work up:
1. `comma_csv_parser.py` -- Standard CSV with headers
2. `pipe_csv_parser.py` -- Same as CSV but pipe-delimited
3. `json_parser.py` -- JSON array of record objects
4. `xml_parser.py` -- XML with `<filing>` elements
5. `fixed_width_parser.py` -- Column-position parsing

### Step 3: Implement the Validation Checks

Open each file in `checks/` and complete the TODOs. Each check function receives keyword arguments (`state`, `source_file`, `source_records`, `bronze_records`, `parse_error`, `expected_count`) and returns a result dict with `check_id`, `check_name`, `status` (PASS/FAIL/WARN), `message`, and `details`.

Start with `source_checks.py` (SRC-01) since it is the simplest, then work through the rest in order.

### Step 4: Implement the State Tester

Open `state_tester.py` and complete all TODOs:

1. **`parse_source()`** -- Get the parser via `get_parser()`, call it, store results, handle exceptions
2. **`run_checks()`** -- Iterate over `ALL_CHECKS`, call each with the standard kwargs, catch exceptions
3. **`run()`** -- Orchestrate: parse first, then run checks, build summary counts, return result dict

### Step 5: Implement the Coordinator

Open `coordinator.py` and complete all TODOs:

1. **`load_manifest()`** -- Read `load_manifest.json`
2. **`load_bronze_table()`** -- Read `bronze_table.json`
3. **`get_bronze_records_for_state()`** -- Filter records by state code
4. **`run_state_test()`** -- Create a `StateTester` instance and call `.run()`
5. **`run_parallel()`** -- Use `ThreadPoolExecutor` to run all state tests concurrently
6. **`run()`** -- Full pipeline: load data, run parallel tests, generate dashboard

### Step 6: Implement the Dashboard

Open `dashboard.py` and complete all TODOs:

1. **`get_summary()`** -- Aggregate pass/fail/warn counts across all states
2. **`print_console()`** -- Formatted table with state rows, totals, and failure details
3. **`generate_html()`** -- Styled HTML report with color-coded cells (green=pass, red=fail, yellow=warn)
4. **`generate_json()`** (bonus) -- Machine-readable JSON report

### Step 7: Run Full Seed Validation

```bash
cd starter
python coordinator.py --data-dir mock_data --workers 5
```

Expected output:
- 11 states CLEAN (all 12 checks pass)
- GA with ERRORS (DT-01 fails -- dates are DD/MM/YYYY, not YYYY-MM-DD)
- NY with ERRORS (DT-02 fails -- 2 records whose lapse date precedes their filing date)
- NV with WARNINGS (DUP-01 warns on 3 duplicate filing numbers)
- TX_BAD with ERRORS (SRC-01 fails -- truncated file)
- FL_BAD with ERRORS (SRC-01 fails -- encoding error)

That is 11 clean + 5 flagged = 16. The JSON summary counts `states_clean: 12`
because it counts states with zero *failures*, and NV's duplicate is a warning
rather than a failure -- two defensible tallies of the same run, so read the
definition before comparing the numbers.

Compare your console output against `expected_output/full_seed_dashboard.txt`.

### Step 8: Run with Error Files

The two error files test your agent's resilience:

- **TX_BAD_truncated.dat** -- A fixed-width file cut off mid-record. Your parser should raise an exception, and the state tester should gracefully record SRC-01 as FAIL and continue running the remaining checks.
- **FL_BAD_encoding.json** -- A JSON file saved with UTF-16LE BOM encoding. Your parser should fail to decode it, and the state tester should handle the error.

Verify that:
1. The coordinator does not crash when individual state testers encounter errors
2. The dashboard shows TX_BAD and FL_BAD with appropriate failure messages
3. Other states are unaffected by the failures

### Step 9: Deploy Locally with Docker

```bash
# From the starter directory
docker build -t bronze-validator .
docker run -v $(pwd)/mock_data:/data/mock_data bronze-validator

# Or use docker compose (from the solution directory)
cd ../solution
docker compose up --build
```

---

## Final Verification

Compare your output against the files in `expected_output/`. Your system should:

- [ ] Parse all 5 file formats correctly (XML, pipe CSV, comma CSV, fixed-width, JSON)
- [ ] Run all 12 validation checks for each of 16 states
- [ ] Execute state tests in parallel using ThreadPoolExecutor
- [ ] Detect GA date format issues (DT-01 FAIL, DT-02 FAIL)
- [ ] Detect NV duplicate filing numbers (DUP-01 WARN)
- [ ] Handle TX_BAD truncated file gracefully (SRC-01 FAIL)
- [ ] Handle FL_BAD encoding error gracefully (SRC-01 FAIL)
- [ ] Generate console dashboard with per-state pass/fail/warn counts
- [ ] Generate HTML report with color-coded cells
- [ ] Not crash when individual states fail
- [ ] Exit with non-zero code when any failures are detected

---

## What You Built

By completing this capstone, you have built:

1. **A coordinator agent** that orchestrates parallel subagent execution
2. **16 state tester subagents** that each validate one state's data independently
3. **5 file format parsers** for XML, pipe-delimited CSV, comma CSV, fixed-width, and JSON
4. **12 validation checks** covering source integrity, counts, schema, dates, names, metadata, and spot checks
5. **A multi-format dashboard** generating console, HTML, and JSON reports
6. **Error-resilient architecture** where individual state failures do not crash the coordinator

These patterns directly apply to production data engineering pipelines: ETL validation, data quality monitoring, and multi-source ingestion testing.

---

## Running the Tests

```bash
# From the capstone root directory
pip install pytest
pytest tests/ -v
```

---

## Solution Reference

If you get stuck, the `solution/` directory contains fully implemented versions of all files. The solution's `mock_data/` directory references the same test data as the starter.

**Note:** The solution directory uses the same `mock_data/` from `starter/` for source files and Bronze table data. When running the solution, pass the path to the starter's mock_data:

```bash
cd solution
python coordinator.py --data-dir ../starter/mock_data
```

---

## Next Steps

Continue to **Module M22B: Deployment Lab** where you will deploy this validation agent to Local Docker, GCP Cloud Run, and AWS Lambda with monitoring and observability. The `solution/deploy/` directory contains starter deployment configurations for all three tiers.
