# M16: Input Guardrails — Lab

## What You'll Build
An input validation pipeline that protects your UCC agent from malicious inputs, PII leakage, and malformed requests.

## Prerequisites
- Completed M05 (Function Calling) and M12 (Multi-Agent Systems)
- Python 3.10+ or Node.js 18+
- Anthropic API key configured

## Setup
```bash
cd labs/M16-input-guardrails
# Python
pip install -r ../../requirements.txt
# Node.js
npm install --prefix ../..
```

## Lab Steps

### Step 1: Build the PII Detector (15 min)
Open `starter/pii_detector.py` (or `starter/pii_detector.js` for Node.js).

You'll implement regex patterns to detect five types of PII:
- Social Security Numbers (XXX-XX-XXXX)
- Credit card numbers (16 digits, with or without separators)
- Email addresses
- Phone numbers (multiple formats)
- Dates of birth (MM/DD/YYYY and YYYY-MM-DD)

Fill in TODOs 1-6 to complete the `detect_pii()` function that scans text, finds matches, and returns redacted output.

**Test your work:**
```bash
python starter/pii_detector.py
# or
node starter/pii_detector.js
```

### Step 2: Build the Injection Filter (15 min)
Open `starter/injection_filter.py` (or `starter/injection_filter.js`).

You'll implement pattern matching for two categories of prompt injection:
- **Direct injection**: "ignore previous instructions", role-switching, system prompt extraction, delimiter-based overrides
- **Indirect injection**: hidden XML-style instructions in tool results, base64-encoded payloads

Fill in TODOs 1-10 to build the `check_injection()` function that classifies inputs by risk level (none/low/medium/high).

**Test your work:**
```bash
python starter/injection_filter.py
# or
node starter/injection_filter.js
```

### Step 3: Build the Schema Validator (10 min)
Open `starter/schema_validator.py` (or `starter/schema_validator.js`).

You'll validate UCC-specific data formats:
- Filing numbers: `UCC-YYYY-SS-NNNNNNN` (year range, valid state codes, sequence length)
- Search queries: debtor name length/content, state codes, filing types, status values

Fill in TODOs 1-6 to build `validate_filing_number()` and `validate_search_query()`.

**Test your work:**
```bash
python starter/schema_validator.py
# or
node starter/schema_validator.js
```

### Step 4: Wire the Validation Pipeline (15 min)
Open `starter/validation_pipeline.py` (or `starter/validation_pipeline.js`).

You'll compose all three guards into a single pipeline that:
1. Checks for PII and redacts it (warn, don't block)
2. Checks for prompt injection (block if high risk)
3. Validates schema if a structured query is provided (block if invalid)

Fill in TODOs 1-5 to build `validate_input()`.

**Test your work:**
```bash
python starter/validation_pipeline.py
# or
node starter/validation_pipeline.js
```

### Step 5: Test with Adversarial Inputs (10 min)
Run the full test suite against 10+ adversarial inputs. The pipeline runner includes tests for:
1. Clean input (should pass)
2. PII in query (should warn and redact)
3. Direct prompt injection (should block)
4. SQL injection in structured query (should block)
5. Invalid state code (should block)
6. Role-switching attempt (should block)
7. Credit card number (should warn and redact)
8. Indirect injection from tool result (should block)
9. Multiple issues combined (should block)
10. Delimiter-based injection (should block)

Compare your output against `expected_output/validation_output.txt`.

## Final Verification
```bash
# Run the solution to see expected behavior
python solution/validation_pipeline.py
# or
node solution/validation_pipeline.js
```

## What You Built
- PII detector catching SSN, credit card, phone, email, and date-of-birth patterns
- Prompt injection filter blocking direct and indirect injection attempts
- Schema validator enforcing UCC filing formats and search query constraints
- Complete validation pipeline composing all three guards with allow/block/warn logic

## Next
-> M17: Output Guardrails & Human-in-the-Loop
